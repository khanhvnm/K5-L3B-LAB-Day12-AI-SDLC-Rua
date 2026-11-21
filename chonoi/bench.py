"""Benchmark có render (Test Contract v1.3, TICKET-04): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (gather, preset chuẩn: độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định), Út Sen đứng yên ở
bến, cửa sổ 1280×720. Mô phỏng chạy bằng `LiveGame` như bản chơi thường; trang `chonoi/web/index.html` ở chế độ
`?bench=<giây>&warmup=<giây>` vẽ Canvas trong trình duyệt Chromium headless (Chrome/Chromium/Edge), làm nóng rồi đo
thời gian từng khung bằng `requestAnimationFrame` và gửi về `POST /bench`. Python tính và ghi:

    {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}

- frames, measured_s: số khung và số giây thực tế trong khoảng đo sau làm nóng.
- avg_fps = frames / measured_s.
- p1_low_fps: lấy max(1, ceil(0.01 × frames)) khung chậm nhất, nghịch đảo thời gian trung bình (giây) của chúng.
- load_ms: từ lúc khởi chạy lệnh tới khung hình đầu tiên của cảnh đo.

Trình duyệt: biến môi trường CHONOI_BROWSER, rồi các tên/đường dẫn chuẩn trên Linux/macOS/Windows.
Mã thoát: 0 ghi xong; 2 tham số sai; 1 không có trình duyệt / quá thời gian / lỗi ghi (không bịa số).
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

T0 = time.time()  # mốc "khởi chạy" cho load_ms (epoch, cùng đồng hồ với trang)

from .contract import load_contract  # noqa: E402
from .live import LiveGame, LiveServer, _Handler  # noqa: E402

WIDTH, HEIGHT = 1280, 720
WARMUP_S = 3
MAX_BENCH_BODY = 8 * 1024 * 1024
BROWSER_NAMES = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome",
                 "microsoft-edge", "microsoft-edge-stable", "msedge")
BROWSER_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


class BenchError(Exception):
    pass


# --- tính số liệu (hàm thuần, có test) ---------------------------------------------------
def compute_metrics(frame_ms, measured_ms, first_frame_epoch_ms, start_epoch_s=T0) -> dict:
    """`frame_ms`: thời gian từng khung (ms) trong khoảng đo; `measured_ms`: độ dài khoảng đo thực tế."""
    if not frame_ms or measured_ms <= 0:
        raise BenchError("không ghi được khung hình nào trong khoảng đo")
    frames = len(frame_ms)
    measured_s = measured_ms / 1000.0
    n = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_ms, reverse=True)[:n]
    slow_avg_s = sum(slowest) / n / 1000.0
    return {
        "avg_fps": round(frames / measured_s, 2),
        "p1_low_fps": round(1.0 / slow_avg_s, 2) if slow_avg_s > 0 else 0.0,
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": max(0, round(first_frame_epoch_ms - start_epoch_s * 1000.0)),
    }


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env:
        path = shutil.which(env) or (env if os.path.isfile(env) else None)
        if not path:
            raise BenchError(f"CHONOI_BROWSER={env!r} không tìm thấy")
        return path
    for name in BROWSER_NAMES:
        path = shutil.which(name)
        if path:
            return path
    for path in BROWSER_PATHS:
        if os.path.isfile(path):
            return path
    raise BenchError("không tìm thấy trình duyệt Chromium/Chrome/Edge; đặt CHONOI_BROWSER=<đường dẫn>")


# --- máy chủ bench -----------------------------------------------------------------------
class _BenchHandler(_Handler):
    result = None  # dict dùng chung, gán trên lớp con
    done = None    # threading.Event

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/bench":
            return super().do_POST()
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= MAX_BENCH_BODY:
                raise ValueError("body sai")
            body = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("body phải là object")
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.result.update(body)
        self.done.set()
        self._send(200, b'{"ok":true}')


def run_bench(seed, duration, browser, warmup=WARMUP_S, timeout_extra=60):
    tuning = load_contract()["tuning"]
    game = LiveGame("gather", tuning, {}, seed)  # Út Sen xuất phát ở bến, không input -> đứng yên
    server = LiveServer(game, "127.0.0.1", 0)
    result, done = {}, threading.Event()
    server.httpd.RequestHandlerClass = type("BenchHandler", (_BenchHandler,),
                                            {"game": game, "result": result, "done": done})
    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    proc = None
    try:
        server.start()
        url = f"{server.url}?bench={duration}&warmup={warmup}"
        args = [browser, "--headless=new", f"--window-size={WIDTH},{HEIGHT}", f"--user-data-dir={profile}",
                "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--mute-audio",
                "--disable-gpu-vsync", "--disable-frame-rate-limit", "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows"]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            args.append("--no-sandbox")  # container chạy root
        proc = subprocess.Popen(args + [url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not done.wait(warmup + duration + timeout_extra):
            raise BenchError("quá thời gian chờ kết quả từ trình duyệt")
        return compute_metrics(result.get("frame_ms") or [], float(result.get("measured_ms") or 0),
                               float(result.get("first_frame_epoch_ms") or 0))
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        server.stop()
        shutil.rmtree(profile, ignore_errors=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark có render cảnh lặn (Test Contract v1.3).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True, help="số giây đo sau 3 s làm nóng")
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not a.duration > 0:
        sys.stderr.write("--duration phải > 0\n")
        return 2
    try:
        metrics = run_bench(a.seed, a.duration, find_browser())
    except BenchError as e:
        sys.stderr.write(f"bench lỗi: {e}\n")
        return 1
    try:
        d = os.path.dirname(os.path.abspath(a.out))
        fd, tmp = tempfile.mkstemp(prefix=".bench-", suffix=".tmp", dir=d)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(metrics, f, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, a.out)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps(metrics), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

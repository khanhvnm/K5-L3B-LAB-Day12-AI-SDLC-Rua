"""Clone sạch và smoke HTTP/UI, sau đó thử lại với file bàn giao chưa commit.

python3 tools/proof_clean_clone.py — không cài dependency, không sửa clone gốc.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def smoke(directory):
    proc = subprocess.Popen([sys.executable, '-u', '-m', 'chonoi.live', '--mode', 'day', '--days', '5', '--port', '0'],
        cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    try:
        # Đọc dòng startup có timeout để lỗi server không treo kiểm chứng.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            line = executor.submit(proc.stdout.readline).result(timeout=15)
        url = next(word for word in line.split() if word.startswith('http://'))
        def get(path):
            with urllib.request.urlopen(url + path, timeout=5) as response:
                return response.read()
        state = json.loads(get('state'))
        assert state['screen'] == 'menu' and state['day'] == 1, state
        page = get('?contrast=high').decode('utf-8')
        assert '<canvas' in page
        req = urllib.request.Request(url + 'advance', data=json.dumps({'screen_id': state['screen_id']}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=5).close()
        state = json.loads(get('state'))
        assert state['screen'] == 'day_intro', state
        return 'HTTP 200: Canvas, menu Ngày 1, POST /advance -> day_intro; không cài pip/npm.'
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main():
    url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, text=True).strip()
    with tempfile.TemporaryDirectory(prefix='.p4-day-ui-check-', dir=ROOT) as tmp:
        clone = Path(tmp) / 'clone'
        subprocess.run(['git', 'clone', '--depth', '1', '--branch', 'main', url, str(clone)], check=True)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=clone, text=True).strip()
        assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=clone)
        print('CLEAN MAIN', commit, smoke(clone), flush=True)
        # File runtime/doc mới chưa được commit: overlay chính xác file từ lát bàn giao,
        # tách kết quả này khỏi clone sạch main để không nhận nhầm bằng chứng.
        for name in ['chonoi/web/index.html', 'README.md', 'LICENSE', 'CREDITS.md']:
            shutil.copy2(ROOT / name, clone / name)
        print('HANDOFF OVERLAY', smoke(clone), flush=True)
        print('TEMP cleaned on exit', flush=True)


if __name__ == '__main__':
    main()

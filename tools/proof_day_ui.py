"""Chrome thật + fixture hợp lệ; chụp proof P4, không cần thư viện ngoài.

Chạy tại gốc repo: python3 tools/proof_day_ui.py
Node có WebSocket (22+) chỉ cần cho công cụ kiểm chứng này, không cần khi chơi.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chonoi.bench import find_browser
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from chonoi.scenario import load_scenario


CDP = r'''
const fs = require('node:fs');
(async () => {
  const [port, url, output] = process.argv.slice(2);
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const ws = new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const [ok,no]=pending.get(m.id);pending.delete(m.id);m.error?no(Error(m.error.message)):ok(m.result);}};
  const call=(method,params={})=>new Promise((ok,no)=>{pending.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{
    const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if(r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  await call('Emulation.setDeviceMetricsOverride',{width:1280,height:720,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url});
  for(let n=0;n<100;n++){
    if(await evaluate('typeof snap !== "undefined" && snap !== null')) break;
    await new Promise(r=>setTimeout(r,100));
  }
  if(!await evaluate('highContrast && snap !== null')) throw Error('contrast/state not ready');
  // Input thật qua sự kiện bàn phím của Chrome; kiểm hai lần H và lưu lựa chọn.
  for(let i=0;i<2;i++) {
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'h',code:'KeyH'});
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'h',code:'KeyH'});
  }
  if(!await evaluate('highContrast && localStorage.getItem(CONTRAST_KEY)==="high"')) throw Error('H/storage failed');
  const warnings = await evaluate(`(() => {
    const labels=[]; const original=ctx.fillText;
    ctx.fillText=function(value,...args){labels.push(value);return original.call(this,value,...args);};
    try { frame(); } finally { ctx.fillText=original; }
    const pixel=Array.from(ctx.getImageData(100,600,1,1).data);
    if(pixel.slice(0,3).some(v=>v!==0)) throw Error('Canvas background must be black');
    return labels;
  })()`);
  const expected=output.includes('oxygen')?'⚠ Sắp hết hơi!':output.includes('monster')?'⚠ Thủy quái!':'⚠ Sắp giận!';
  if(!warnings.includes(expected)) throw Error(`missing warning ${expected}`);
  const shot=await call('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(output,Buffer.from(shot.data,'base64'));
  console.log(JSON.stringify({output,state:await evaluate('({phase:phaseOf(snap),tick:snap.tick,player:snap.player,customers:snap.customers,highContrast})')}));
  ws.close();
})().catch(e=>{console.error(e);process.exit(1);});
'''


def main():
    tuning = load_contract()['tuning']
    fixtures = {
        'oxygen': ('gather', {'player': {'pos': [40, 10], 'oxygen_ticks': 400}, 'monsters': []}),
        'monster': ('gather', {'player': {'pos': [55, 24]}}),
        'patience': ('quan', {'random_customers': False, 'customers': [
            {'id': 'C1', 'table_id': 'T1', 'dish_id': 'ca_loc_nuong_trui', 'patience_ticks_left': 800}]}),
    }
    # TemporaryDirectory dọn cả khi kiểm chứng lỗi; không xóa thư mục có sẵn.
    with tempfile.TemporaryDirectory(prefix='.p4-day-ui-check-', dir=ROOT) as temp:
        temp = Path(temp)
        driver = temp / 'capture.cjs'
        driver.write_text(CDP, encoding='utf-8')
        for name, (mode, block) in fixtures.items():
            fixture = temp / 'scenario.json'
            fixture.write_text(json.dumps({mode: block}), encoding='utf-8')
            game = LiveGame(mode, tuning, load_scenario(str(fixture), mode, tuning), 42)
            # Một bước mô phỏng thật; giữ khung ở tick này để ảnh tái lập được.
            game._tick_once()
            game.start = lambda: None
            server = LiveServer(game, '127.0.0.1', 0)
            profile = temp / name
            proc = None
            try:
                server.start()
                proc = subprocess.Popen([find_browser(), '--headless=new', '--remote-debugging-port=0',
                    f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check', 'about:blank'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                portfile = profile / 'DevToolsActivePort'
                deadline = time.monotonic() + 20
                while not portfile.exists():
                    if time.monotonic() > deadline:
                        raise RuntimeError('Chrome CDP timeout')
                    time.sleep(.1)
                subprocess.run(['node', str(driver), portfile.read_text().splitlines()[0],
                    server.url + '?contrast=high', str(ROOT / 'docs/proof/phase-4' / f'contrast-{name}.png')],
                    check=True, timeout=30)
            finally:
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                server.stop()


if __name__ == '__main__':
    main()

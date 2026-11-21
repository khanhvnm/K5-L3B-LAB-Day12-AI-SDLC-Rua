// Chạy bằng node --test tests/test_ui.js, không cần package ngoài.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../chonoi/web/index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
function client(fetchOverride) {
  const handlers = {}, calls = [], labels = [], fonts = [], timers = new Map();
  let timerId = 0;
  const context2d = new Proxy({}, {get: (target, key) => key === 'measureText' ? s => ({width: String(s).length * 7}) : key === 'createLinearGradient' ? () => ({addColorStop(){}}) : key === 'fillText' ? s => {labels.push(s); fonts.push(target.font);} : () => {}, set: Reflect.set});
  function element(tag) {
    return {tag, children: [], handlers: {}, getContext: () => context2d, appendChild(el) {this.children.push(el);},
      replaceChildren(){this.children = [];}, addEventListener(name, fn){this.handlers[name] = fn;},
      querySelector(){return this.children.find(el => el.tag === 'button' && !el.disabled);}, focus(){}, setAttribute(){}};
  }
  const elements = {c: element('canvas'), panel: element('section'), screen: element('div')};
  const context = vm.createContext({innerWidth: 1280, innerHeight: 720, window: {devicePixelRatio: 1},
    document: {getElementById: id => elements[id], createElement: element},
    addEventListener: (name, callback) => handlers[name] = callback,
    requestAnimationFrame(){}, setTimeout(fn, ms){timers.set(++timerId, {fn, ms}); return timerId;},
    clearTimeout(id){timers.delete(id);},
    fetch: async (url, options) => {calls.push({url, options}); return fetchOverride ? fetchOverride(url, options) : {ok: true, json: async () => ({mode: 'gather', events: []})};}});
  vm.runInContext(script, context);
  const run = code => vm.runInContext(code, context);
  const key = (type, value) => handlers[type]({key: value, preventDefault(){}, repeat: false});
  const panelText = () => elements.panel.children.map(el => el.textContent);
  const click = label => elements.panel.children.find(el => el.textContent.includes(label)).handlers.click();
  return {run, key, handlers, calls, labels, fonts, timers, panelText, click};
}
test('giữ hai phím cùng hướng rồi nhả một vẫn di chuyển', () => {
  const c = client(); c.key('keydown','w'); c.key('keydown','ArrowUp'); c.key('keyup','w');
  assert.equal(c.run('currentInput().move[1]'), -1);
  c.handlers.blur(); assert.equal(c.run('currentInput().move[1]'), 0);
});
test('quán đảo trục z và không gửi catch', () => {
  const c = client(); c.run('snap={mode:"quan"}'); c.key('keydown','w'); c.key('keydown',' ');
  assert.equal(c.run('currentInput().move[1]'), 1); assert.equal(c.run('currentInput().catch'), false);
});
test('tên món dạng chuỗi và object', () => {
  const c = client(); assert.equal(c.run('dishName({dish_id:"goi_bong_sung"})'), 'Gỏi bông súng');
  assert.equal(c.run('dishName("ca_loc_nuong_trui")'), 'Cá lóc nướng trui');
  assert.equal(c.run('dishName(null)'), 'Chưa có dữ liệu');
});
test('sự kiện dùng yield, free, required và không thông báo lặp', () => {
  const c = client();
  c.run('consumeEvents([{tick:1,name:"fish_caught",data:{kind:"ca_linh",yield:3}}])');
  c.run('consumeEvents([{tick:1,name:"fish_caught",data:{kind:"ca_linh",yield:3}}])');
  assert.equal(c.run('messages.length'),1); assert.match(c.run('messages[0]'),/×3/);
  assert.match(c.run('eventMessage({name:"hold_full",data:{free:1,required:3}})'), /1 trống.*3/);
});
test('HUD hai mode không lỗi khi thiếu trường tùy chọn', () => {
  const c = client();
  c.run('snap={mode:"gather",player:{pos:[2,0]},time_left_ticks:60}; drawGather(800,600); overlay(800,600)');
  c.run('snap={mode:"quan",player:{pos:[8,5]},stoves:[{id:"B1",pos:[2,8],state:"ready",dish:{dish_id:"goi_bong_sung"}}]}; drawQuan(800,600)');
  assert.ok(c.labels.includes('Gỏi bông súng')); assert.ok(!c.labels.includes('[object Object]'));
});
test('HTTP lỗi không được xem là thành công', async () => {
  const c = client(async () => ({ok:false,status:503}));
  await assert.rejects(c.run('checkedFetch("/input")'), /503/);
});

test('day điều khiển theo pha, Escape gửi cạnh xung và không bơi khi pause', async () => {
  const c = client();
  await new Promise(setImmediate);
  c.run('snap={mode:"day",phase:"quan",screen:"playing"}');
  c.key('keydown','w'); c.key('keydown','Escape');
  await new Promise(setImmediate);
  const commands = c.calls.filter(call => call.url === '/input').map(call => JSON.parse(call.options.body));
  assert.ok(commands.some(cmd => cmd.move[1] === 1 && !cmd.catch));
  assert.deepEqual(commands.filter(cmd => 'pause' in cmd).map(cmd => cmd.pause), [true, false]);
  c.run('snap.state="paused"; updatePanel()');
  c.key('keydown', 's');
  assert.equal(c.run('currentInput().move[1]'), 0);
  assert.ok(c.panelText().includes('Tiếp tục'));
  assert.ok(c.panelText().includes('Về menu'));
});

test('DayIntro tự chuyển sau 4 giây, EveningIntro dùng kho khả dụng, có DayResult và Summary', async () => {
  const c = client();
  await new Promise(setImmediate);
  c.run(`acceptState({screen:"day_intro",screen_id:1,day:1,day_plan:{
    ingredients:{ca_loc:3},dishes:{ca_loc_nuong_trui:3}}}); updatePanel()`);
  assert.ok(c.panelText().some(line => /Cần lấy: cá lóc ×3/.test(line)));
  const intro = [...c.timers.values()].find(timer => timer.ms === 4000);
  assert.ok(intro);
  intro.fn();
  await new Promise(setImmediate);
  assert.equal(c.calls.find(call => call.url === '/advance').options.body, '{"screen_id":1}');
  c.run(`snap={screen:"evening_intro",screen_id:2,day:1,delivered:{ca_loc:1},available_stock:{},
    day_plan:{dishes:{ca_loc_nuong_trui:3}},menu:{ca_loc_nuong_trui:{recipe:{ca_loc:1}}}}; updatePanel()`);
  assert.ok(c.panelText().includes('Đã nhập kho: cá lóc ×1'));
  assert.ok(c.panelText().some(line => /chưa đủ/.test(line)));
  c.run(`snap={screen:"day_result",screen_id:3,day:1,money:72,
    day_result:{served:1,left:0,tips:12,earned:72,reputation_delta:.2}}; updatePanel()`);
  assert.ok(c.panelText().some(line => /Boa 12k.*Uy tín \+0.2/.test(line)));
  c.run(`snap={screen:"summary",screen_id:4,money:72,earned:72,score:372,reputation:3.2,
    dishes_sold:{ca_loc_nuong_trui:3,goi_bong_sung:1}}; updatePanel()`);
  assert.ok(c.panelText().includes('Món bán chạy: Cá lóc nướng trui ×3'));
});

test('Shop mua từ catalog và gửi cạnh đóng; HUD vẽ chữ từ 18px', async () => {
  const c = client();
  await new Promise(setImmediate);
  c.run(`snap={mode:"day",phase:"shop",screen:"playing",day:2,money:300,upgrades:{oxygen:1},
    meta:{upgrades:{oxygen:[{level:1,price:200},{level:2,price:400,oxygen_max_s:60}]}}}; updatePanel()`);
  assert.ok(c.panelText().includes('Mua Bình oxy cấp 2 · 400k · 60 giây oxy'));
  c.click('Mua Bình oxy');
  c.click('Đóng cửa hàng');
  await new Promise(setImmediate);
  const commands = c.calls.filter(call => call.url === '/input').map(call => JSON.parse(call.options.body));
  assert.equal(commands.filter(cmd => cmd.buy === 'oxygen').length, 1);
  assert.deepEqual(commands.filter(cmd => 'shop_done' in cmd).map(cmd => cmd.shop_done), [true, false]);
  c.run(`snap={mode:"day",phase:"gather",day:2,hold:["ca_loc"],hold_capacity:12,day_plan:{ingredients:{ca_loc:2}},
    player:{pos:[40,10],hp:2,hp_max:3,oxygen_ticks:0,oxygen_max_ticks:1800}}; drawGather(1280,720)`);
  assert.ok(c.labels.includes('Hết hơi!'));
  assert.ok(c.labels.includes('Đã lấy / cần: cá lóc 1/2'));
  assert.ok(c.fonts.every(font => parseInt(font, 10) >= 18));
});
test('restart chờ input đang gửi, bỏ hàng đợi cũ và gửi trạng thái nhả', async () => {
  let release;
  const blocked = new Promise(resolve => release = resolve);
  const c = client(async url => {if(url === '/input') await blocked; return {ok:true,json:async()=>({mode:'gather',events:[]})};});
  c.key('keydown','d'); c.key('keydown','e');
  const restarting = c.run('restart()');
  await Promise.resolve(); assert.ok(!c.calls.some(x=>x.url==='/restart'));
  release(); await restarting; await c.run('flush()');
  assert.equal(c.run('queue.length'),0);
  const inputs=c.calls.filter(x=>x.url==='/input').map(x=>JSON.parse(x.options.body));
  assert.equal(inputs.length,2); assert.deepEqual(inputs[1],{move:[0,0],interact:false,catch:false});
});

// Chạy bằng node --test tests/test_ui.js, không cần package ngoài.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../chonoi/web/index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
function client(fetchOverride) {
  const handlers = {}, calls = [], labels = [];
  const context2d = new Proxy({}, {get: (_, key) => key === 'measureText' ? s => ({width: String(s).length * 7}) : key === 'createLinearGradient' ? () => ({addColorStop(){}}) : key === 'fillText' ? s => labels.push(s) : () => {}, set: () => true});
  const context = vm.createContext({innerWidth: 800, innerHeight: 600, window: {devicePixelRatio: 1},
    document: {getElementById: () => ({getContext: () => context2d})},
    addEventListener: (name, callback) => handlers[name] = callback,
    requestAnimationFrame(){}, setTimeout(){},
    fetch: async (url, options) => {calls.push({url, options}); return fetchOverride ? fetchOverride(url, options) : {ok: true, json: async () => ({mode: 'gather', events: []})};}});
  vm.runInContext(script, context);
  const run = code => vm.runInContext(code, context);
  const key = (type, value) => handlers[type]({key: value, preventDefault(){}, repeat: false});
  return {run, key, handlers, calls, labels};
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

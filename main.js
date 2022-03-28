const websocket = new WebSocket('wss://hermy-games-websockets.herokuapp.com/');
const butt = document.querySelector('#butt');
const fromX = document.querySelector('#fx');
const fromY = document.querySelector('#fy');
const toX = document.querySelector('#tx');
const toY = document.querySelector('#ty');
const capturing = document.querySelector('#capturing');

websocket.addEventListener('open', () => {
  websocket.send(JSON.stringify({type: 'join', token: '2'}))
})


const reverse = (value) => {
  return Math.abs(Number(value) - 7);
}

butt.addEventListener('click', () => {
  const message = {from: {x: reverse(fx.value), y: reverse(fy.value)}, to: {x: reverse(tx.value), y: reverse(ty.value)}, capturing: capturing.checked, colour: "black"}
  const event = { type: 'move', content: JSON.stringify(message) };
  // console.log(message)
  websocket.send(JSON.stringify(event));
});

websocket.addEventListener('message', ({ data }) => {
  const event = JSON.parse(data);
  window.setTimeout(() => console.log(event), 50);
});

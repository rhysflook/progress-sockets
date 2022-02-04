const websocket = new WebSocket('ws://localhost:8001/');
const butt = document.querySelector('#button');
const message = document.querySelector('#message');

butt.addEventListener('click', () => {
  const event = { type: 'message', content: message.value };
  websocket.send(JSON.stringify(event));
});

websocket.addEventListener('message', ({ data }) => {
  const event = JSON.parse(data);
  window.setTimeout(() => console.log(event), 50);
});

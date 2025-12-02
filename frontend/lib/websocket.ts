export const connectWebSocket = (
  onMessage: (msg: any) => void,
  onClose: () => void
) => {
  const ws = new WebSocket("ws://localhost:8000/ws/transcribe/");

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onclose = onClose;

  return ws;
};
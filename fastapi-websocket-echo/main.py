from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Serve the HTML client
html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
</head>
<body>
    <h2>WebSocket Echo Test</h2>

    <input id="messageInput" type="text" placeholder="Enter message">
    <button onclick="sendMessage()">Send</button>

    <h3>Messages</h3>
    <ul id="messages"></ul>

    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");

        ws.onmessage = function(event) {
            const li = document.createElement("li");
            li.textContent = event.data;
            document.getElementById("messages").appendChild(li);
        };

        function sendMessage() {
            const input = document.getElementById("messageInput");
            ws.send(input.value);
            input.value = "";
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive text message from client
            data = await websocket.receive_text()
            # Send back formatted response
            await websocket.send_text(f"Server received: {data}")
    except WebSocketDisconnect:
        # Print disconnection message to server terminal
        print("Client disconnected")
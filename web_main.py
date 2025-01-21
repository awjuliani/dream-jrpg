import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from src.game.jrpg import JRPG
from src.game.response_manager import ResponseManager
import os
import asyncio
import traceback

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")
# check if images folder exists, if not create it
if not os.path.exists("images"):
    os.makedirs("images")
app.mount("/images", StaticFiles(directory="images"), name="images")

# Initialize game instances
response_manager = ResponseManager()
jrpg = JRPG()
game_task = None


async def handle_game_task_exception(task):
    try:
        await task
    except Exception as e:
        print(f"Error in game task: {e}")
        print(traceback.format_exc())


@app.on_event("startup")
async def startup_event():
    global game_task
    game_task = asyncio.create_task(jrpg.run_game())
    asyncio.create_task(handle_game_task_exception(game_task))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    response_manager.set_websocket(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")
            if action == "menu_option" or action == "text_input":
                response = (
                    message.get("option")
                    if action == "menu_option"
                    else message.get("text")
                )
                response_manager.set_player_response(response=response)
            elif action == "get_game_state":
                response = response_manager.get_game_response()
                await websocket.send_json(response)
            else:
                response = {"error": "Invalid action"}
                await websocket.send_json(response)
    except WebSocketDisconnect:
        print("Client disconnected")


# Serve index.html at the root
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")


# Fallback route for other paths
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    frontend_path = os.path.join("frontend", full_path)
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return FileResponse("frontend/index.html")

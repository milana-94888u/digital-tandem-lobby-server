import asyncio
import random
import json

from fastapi import FastAPI, WebSocket

from broadcaster import Broadcaster
from room_producer import create_room

app = FastAPI()
broadcaster = Broadcaster()


players_list = {}


def revert_role(role: str) -> str:
    if role == "mech":
        return "virus"
    elif role == "virus":
        return "mech"
    return "unset"


async def match_players(first: str, second: str) -> None:
    player1 = players_list[first]
    player2 = players_list[second]
    if player1["role"] == player2["role"]:
        if random.randint(0, 1):
            player1["role"] = "mech"
            player2["role"] = "virus"
        else:
            player1["role"] = "virus"
            player2["role"] = "mech"
    elif player1["role"] == "unset":
        player1["role"] = revert_role(player2["role"])
    elif player2["role"] == "unset":
        player2["role"] = revert_role(player1["role"])

    host, port = await create_room()
    await broadcaster.publish({
        "action": "room_created",
        "player": player1,
        "connection_info": {"host": host, "port": port},
    })
    await broadcaster.publish({
        "action": "room_created",
        "player": player2,
        "connection_info": {"host": host, "port": port},
    })


async def ws_sender_task(socket: WebSocket):
    for player in players_list:
        await socket.send_json({"action": "joined", "player": players_list[player]})
    async for message in broadcaster.subscribe():
        await socket.send_json(message)


@app.websocket("/ws/{nickname}/{role}")
async def websocket_endpoint(websocket: WebSocket, nickname: str, role: str) -> None:
    await websocket.accept()
    player = {"nickname": nickname, "role": role}
    if nickname in players_list:
        await websocket.close(reason="existing_nickname")
        return

    await broadcaster.publish({"action": "joined", "player": player})
    players_list[nickname] = player

    loop = asyncio.get_event_loop()
    sender_task = loop.create_task(ws_sender_task(websocket))
    try:
        async for message in websocket.iter_bytes():
            message = json.loads(message.decode("ascii"))
            if message["action"] == "player_chosen":
                await broadcaster.publish({
                    "action": "game_suggested",
                    "proposer": player["nickname"],
                    "receiver": message["nickname"],
                })
            elif message["action"] == "game_accepted":
                await match_players(player["nickname"], message["nickname"])
            elif message["action"] == "game_rejected":
                await broadcaster.publish({
                    "action": "game_rejected",
                    "proposer": message["nickname"],
                    "receiver": player["nickname"],
                })
    finally:
        await broadcaster.publish({"action": "left", "player": player})
        players_list.pop(nickname)
        sender_task.cancel()

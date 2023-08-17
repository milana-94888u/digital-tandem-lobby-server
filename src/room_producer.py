import os

import httpx


app_id = os.getenv("HATHORA_APP_ID")
auth_headers = {"authorization": f"Bearer {os.getenv('HATHORA_TOKEN')}"}


async def create_room() -> tuple[str, int]:
    async with httpx.AsyncClient() as client:
        create_response = await client.post(
            f"https://api.hathora.dev/rooms/v2/{app_id}/create",
            json={"region": "London"},
            headers=auth_headers,
        )
        room_info = create_response.json()
        room_id = room_info["roomId"]

        while room_info["status"] != "active":
            connection_info_response = await client.get(
                f"https://api.hathora.dev/rooms/v2/{app_id}/connectioninfo/{room_id}", headers=auth_headers
            )
            room_info = connection_info_response.json()

        port_info = room_info["exposedPort"]
        host = port_info["host"]
        port = port_info["port"]
        return host, port

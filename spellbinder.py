import asyncio
import random
import json
import os
from typing import List
from nio import AsyncClient, RoomMessageText, MatrixRoom
import csv

# File to store the sync token
TOKEN_FILE = "sync_token.json"

def load_since_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            since_token = json.load(f).get("next_batch")
            return since_token
        
    return None

def structure_tao_te_ching():
    struct = {}
    with open("tao_te_ching.csv", newline="") as tao_te_ching:
        csv_reader = csv.reader(tao_te_ching)
        for row in csv_reader:
            if csv_reader.line_num == 1:
                continue
            struct[int(row[0])] = row[1].replace("\\n", "\n")


    return struct

def compute_tao_chapter(args):
    match args:
        case [i]:
            try:
                i = int(i)
                if i >= 1 and i <= 81:
                    return i
                else:
                    pass
            except (ValueError):
                pass
        case _:
            pass
    
    return random.randint(1, 81)

def compute_command(command: List[str], tao_te_ching):
    match command:
        case ["./tao", *args]:
            chapter = compute_tao_chapter(args)
            response = tao_te_ching[chapter]
            return response

    return None


async def compute_message(room: MatrixRoom, event, client, black_magicians, tao_te_ching):
    
    match event:
        case RoomMessageText():
            if event.sender == client.user_id:
                return
            
            print(f"{event.sender}: {event.body}")

            if any(black_mage in black_magicians for black_mage in black_magicians):
                cmd = list(filter(None, event.body.strip().split(" ")))
                response = compute_command(cmd, tao_te_ching)
                if response != None:
                    await client.room_send(
                        room.room_id,
                        "m.room.message",
                        {"msgtype": "m.text", "body": response}
                    )

async def head():
    home_server = "https://matrix.org"
    username = "spell.binder"
    password = "password"

    client = AsyncClient(home_server, username, proxy="socks5://localhost:8889", ssl=False)

    try:
        await client.login(password)

        # room_id = "#wisewords:matrix.org"
        # await client.join(room_id)

        black_magicians = []
        
        tao_te_ching = structure_tao_te_ching()
        since_token = load_since_token()

        async def _compute_message(room, event):
            await compute_message(room, event, client, black_magicians, tao_te_ching)

        client.add_event_callback(_compute_message, RoomMessageText)

        while True:
            sync_response = await client.sync(timeout=30000, since=since_token)
            with open(TOKEN_FILE, "w") as f:
                json.dump({"next_batch": sync_response.next_batch}, f)
            since_token = sync_response.next_batch

    finally:
        await client.close()

asyncio.run(head())

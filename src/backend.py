

import logging

logging.basicConfig(level = logging.INFO)

import asyncio
import json
import argparse
from websockets import server
from websockets import typing as wstypes
from websockets import exceptions as wsexceptions
import typing
import uuid
import ssl
import pathlib

from proxyutil import *

class Room:
  room_host : server.WebSocketServerProtocol = []
  clients : typing.List[server.WebSocketServerProtocol] = []

rooms : typing.Dict[str, Room] = {}

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

def remove_conn_from_rooms(websocket : server.WebSocketServerProtocol):
  for room in rooms:
    if rooms[room].room_host == websocket:
      rooms[room].room_host = None
    if websocket in rooms[room].clients:
      rooms[room].clients.remove(websocket)
    
async def send_status_response(websocket : server.WebSocketServerProtocol, code : str, id : int, status_code : int, message : str) -> None:
  try:
    msg = Message()
    msg.code = code
    msg.id = id
    msg.msg_type = "status_response"
    msg.has_data = True
    msg.data = { 'status_code': status_code, 'message': message }
    await websocket.send(msg.to_data())
  except wsexceptions.ConnectionClosed as e:
    remove_conn_from_rooms(websocket)
    
async def process_message(websocket : server.WebSocketServerProtocol, rawmsg : wstypes.Data) -> bool:
  msg : Message = Message(rawmsg)
  
  if not msg.code:
    await send_status_response(websocket, 400, f"Improperly formatted message.\n\n{rawmsg}")
  
  if msg.msg_type == "server_subscribe":
    if msg.code not in rooms:
      rooms[msg.code] = Room()
    if not rooms[msg.code].room_host:
      rooms[msg.code].room_host = websocket
      await send_status_response(websocket, msg.code, msg.id, 200, f"Joined room \"{msg.code}\" as host.")
      return True
    else:
      await send_status_response(websocket, "", msg.id, 400, "Room already has a host.")
      return False
  elif msg.msg_type == "client_subscribe":
    if msg.code not in rooms:
      await send_status_response(websocket, "", msg.id, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      rooms[msg.code].clients.append(websocket)
      await send_status_response(websocket, msg.code, msg.id, 200, f"Joined room \"{msg.code}\" as client.")
      return True
    else:
      await send_status_response(websocket, msg.code, msg.id, 409, f"Already in room \"{msg.code}\" as client.")
      return False
  elif msg.msg_type == "await_request":
    if msg.code not in rooms:
      await send_status_response(websocket, "", msg.id, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      await send_status_response(websocket, "", msg.id, 401, f"Invalid room code.")
      return False
    else:
      await rooms[msg.code].room_host.send(msg.to_data())
      await send_status_response(websocket, msg.code, msg.id, 200, f"Sent, wait for response.")
  elif msg.msg_type == "await_response":
    if msg.code not in rooms:
      await send_status_response(websocket, "", msg.id, 401, "Invalid room code.")
      return False
    if rooms[msg.code].room_host != websocket:
      await send_status_response(websocket, "", msg.id, 401, "Invalid room code.")
      return False
    else:
      for client in rooms[msg.code].clients:
        await client.send(msg.to_data())
      await send_status_response(websocket, msg.code, msg.id, 200, "Broadcasted.")
      return True
  elif msg.msg_type == "emit_request":
    if msg.code not in rooms:
      await send_status_response(websocket, "", msg.id, 401, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      await send_status_response(websocket, "", msg.id, 401, 401, f"Invalid room code.")
      return False
    else:
      await rooms[msg.code].room_host.send(msg.to_data())
      await send_status_response(websocket, msg.code, msg.id, 200, "Emitted.")
      return True
      

async def handler(websocket : server.WebSocketServerProtocol):
  while True:
    try:
      message = await websocket.recv()
      
      success = await process_message(websocket, message)
    except:
      remove_conn_from_rooms(websocket)
      break
      
      
async def secure_main(host : str, port : str):
  async with server.serve(handler, host, port, origins = None, ssl = ssl_context):
    await asyncio.Future()
  
  
async def main(host : str, port : str):
  async with server.serve(handler, host, port, origins = None):
    await asyncio.Future()
    
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', '-i', default="127.0.0.1", help="API Host IP")
  parser.add_argument('--port', '-p', type=int, default=8080, help="API Port")
  parser.add_argument('--ssl', '-s', action = "store_true", help = "Enable SSL.")
  parser.add_argument('--fullchain', '-f', help = "Path to fullchain.pem")
  parser.add_argument('--privkey', '-k', help = "Path to the privkey to match fullchain.")
  
  args = parser.parse_args()
  
  if args.ssl:
    fullchain = pathlib.Path(args.fullchain)
    privkey = pathlib.Path(args.privkey)
    ssl_context.load_cert_chain(fullchain, keyfile = privkey)
    asyncio.run(secure_main(args.host, args.port))
  else:
    asyncio.run(main(args.host, args.port))


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

class Room:
  room_host : server.WebSocketServerProtocol = []
  clients : typing.List[server.WebSocketServerProtocol] = []
  
class Message:
  code : str = None
  msg_type : str = None
  hasData : bool = False
  data : dict = None
  
  def __init__(self, data : wstypes.Data):
    try:
      datajson = json.loads(data)
      
      self.code = datajson['code']
      self.msg_type = datajson['msgType']
      self.hasData = datajson['hasData']
      if self.hasData:
        self.data = datajson['data']
    except:
      logging.error("Failed to parse message.")

rooms : typing.Dict[str, Room] = {}

def remove_conn_from_rooms(websocket : server.WebSocketServerProtocol):
  for room in rooms:
    if rooms[room].room_host == websocket:
      rooms[room].room_host = None
    if websocket in rooms[room].clients:
      rooms[room].clients.remove(websocket)
    
async def send_status_response(websocket : server.WebSocketServerProtocol, status_code : int, message : str) -> None:
  try:
    await websocket.send(json.dumps({'status_code': status_code, 'message': message}))
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
      await send_status_response(websocket, 200, f"Joined room \"{msg.code}\" as host.")
      return True
    else:
      await send_status_response(websocket, 400, "Room already has a host.")
      return False
  elif msg.msg_type == "client_subscribe":
    if msg.code not in rooms:
      await send_status_response(websocket, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      rooms[msg.code].clients.append(websocket)
      await send_status_response(websocket, 200, f"Joined room \"{msg.code}\" as client.")
      return True
    else:
      await send_status_response(websocket, 409, f"Already in room \"{msg.code}\" as client.")
      return False
  elif msg.msg_type == "await_request":
    if msg.code not in rooms:
      await send_status_response(websocket, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      await send_status_response(websocket, 401, f"Invalid room code.")
      return False
    else:
      request_id = uuid.uuid4().int
      content = {
        'requestType': 'await',
        'requestId': request_id,
        'request': msg.data
      }
      await rooms[msg.code].room_host.send(json.dumps(content))
      await send_status_response(websocket, 200, f"{request_id}")
  elif msg.msg_type == "await_response":
    if msg.code not in rooms:
      await send_status_response(websocket, 401, "Invalid room code.")
      return False
    if rooms[msg.code].room_host != websocket:
      await send_status_response(websocket, 401, "Invalid room code.")
      return False
    else:
      for client in rooms[msg.code].clients:
        await client.send(json.dumps(msg.data))
      await send_status_response(websocket, 200, "Broadcasted.")
      return True
  elif msg.msg_type == "emit_request":
    if msg.code not in rooms:
      await send_status_response(websocket, 401, "Invalid room code.")
      return False
    if websocket not in rooms[msg.code].clients:
      await send_status_response(websocket, 401, f"Invalid room code.")
      return False
    else:
      request_id = uuid.uuid4().int
      content = {
        'requestType': 'emit',
        'requestId': request_id,
        'request': msg.data
      }
      await rooms[msg.code].room_host.send(json.dumps(content))
      await send_status_response(websocket, 200, "Emitted.")
      return True
      

async def handler(websocket : server.WebSocketServerProtocol):
  while True:
    try:
      message = await websocket.recv()
      
      success = await process_message(websocket, message)
    except:
      remove_conn_from_rooms(websocket)
      break
      
  
async def main(host : str, port : str):
  async with server.serve(handler, host, port):
    await asyncio.Future()
    
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', '-i', default="127.0.0.1", help="API Host IP")
  parser.add_argument('--port', '-p', type=int, default=8080, help="API Port")
  
  args = parser.parse_args()
  asyncio.run(main(args.host, args.port))
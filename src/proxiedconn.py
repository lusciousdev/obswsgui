import asyncio
import logging
import traceback

from websockets import client
from websockets import exceptions as wsexceptions
from websockets import typing as wstypes

import conn
from proxyutil import *

class ProxiedConnection(conn.Connection):
  proxyws : client.WebSocketClientProtocol = None
  timeout = 5.0
  
  async def send_message(self, msg : Message, timeout : float = 5.0) -> Message:
    try:
      await self.proxyws.send(msg.to_data())
      
      return await asyncio.wait_for(self.await_status_response(msg.id), timeout)
    except wsexceptions.ConnectionClosed:
      logging.error("Connection closed.")
      self.connected = False
      return None
    except asyncio.TimeoutError:
      logging.error("Timed out while waiting for a status response.")
      self.connected = False
      return None
    except Exception as e:
      logging.error(f"Error: {e}")
      logging.error(traceback.format_exc())
      return None
  
  async def await_status_response(self, id : int) -> Message:
    while True:
      rawmsg = await self.proxyws.recv()
      
      msg = Message(rawmsg)
      
      if msg.msg_type == "status_response":
        if int(msg.id) == id:
          return msg
    
  async def await_response(self, id : int) -> Message:
    while True:  
      rawmsg = await self.proxyws.recv()
      
      msg = Message(rawmsg)
      
      if msg.id == id:
        if int(msg.id) == id:
          return msg
        else:
          continue
      else:
        continue
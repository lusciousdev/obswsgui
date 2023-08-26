import asyncio
import json
import logging
import traceback

from websockets import client
from websockets import exceptions as wsexceptions
from websockets import typing as wstypes

from .conn import Connection

class Message:
  code : str = None
  id : int = None
  msg_type : str = None
  has_data : bool = False
  data : dict = None
  
  def __init__(self, data : wstypes.Data = None):
    if not data:
      self.code = ""
      self.id = -1
      self.msg_type = ""
      self.has_data = False
      self.data = {}
    else:
      try:
        datajson = json.loads(data)
        
        self.code = datajson['code']
        self.id = datajson['msgId']
        self.msg_type = datajson['msgType']
        self.has_data = datajson['hasData']
        if self.has_data:
          self.data = datajson['data']
      except Exception as e:
        self.code = ""
        self.id = -1
        self.msg_type = ""
        self.has_data = False
        self.data = None
        logging.error(f"Failed to parse message. {e}")
      
  def to_dict(self) -> dict:
    return {
      'code': self.code,
      'msgId': self.id,
      'msgType': self.msg_type,
      'hasData': self.has_data,
      'data': self.data
    }
      
  def to_data(self) -> wstypes.Data:
    return json.dumps(self.to_dict())

class ProxiedConnection(Connection):
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
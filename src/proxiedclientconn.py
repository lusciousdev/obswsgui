import asyncio
import json
import logging
import time
import typing
import uuid
import traceback

import simpleobsws
from websockets import client
from websockets import exceptions as wsexceptions
from websockets import typing as wstypes

import conn
import proxiedconn as pconn

logging.getLogger("websockets.client").setLevel(logging.INFO)

class ProxiedClientConnection(pconn.ProxiedConnection):
  roomcode : str = ""
  
  def __init__(self, url : str, roomcode : str, error_handler : conn.RequestResponseHandler):
    self.url = url
    self.roomcode = roomcode
    
    super().__init__(error_handler)
    
  def request_to_message(self, msgType : str, req : simpleobsws.Request) -> pconn.Message:
    msg = pconn.Message()
    msg.code = self.roomcode
    msg.id = uuid.uuid4().int
    msg.msg_type = msgType
    msg.has_data = True
    msg.data = {
      'requestType': req.requestType,
      'requestData': req.requestData
    }
    
    return msg
  
  async def connect(self) -> bool:
    try:
      self.proxyws = await client.connect(self.url)
      self.connected = True
      
      msg = pconn.Message()
      msg.code = self.roomcode
      msg.id = uuid.uuid4().int
      msg.msg_type = 'client_subscribe'
      msg.has_data = False
      msg.data = {}
      
      resp = await self.send_message(msg, self.timeout)
      
      if resp and resp.data['status_code'] >= 400:
        logging.error(f"Error {resp.data['status_code']}: {resp.data['message']}")
        self.connected = False
      
      return self.connected
    except wsexceptions.InvalidURI:
      logging.error("Invalid URI.")
      self.connected = False
    except OSError:
      logging.error("TCP connection failed.")
      self.connected = True
    except wsexceptions.InvalidHandshake:
      logging.error("Handshake failed.")
      self.connected = False
    except asyncio.TimeoutError:
      logging.error("Handshake timed out")
      self.connected = False
    except wsexceptions.ConnectionClosed:
      logging.error("Connection closed.")
      self.connected = False
    except:
      logging.error("Unknow error encountered while connecting.")
      self.connected = False
      
    return self.connected
    
    
  async def update(self) -> None:
    while True:
      try: # assume messages in buffer are responses from emitted requests
        await asyncio.wait_for(self.proxyws.recv(), 0.001)
      except wsexceptions.ConnectionClosed:
        self.connected = False
        break
      except:
        break
      
    for req in self.request_queue:
      msg = self.request_to_message('emit_request', req)
      
      resp = await self.send_message(msg, self.timeout)
      
      if resp and resp.data['status_code'] >= 400:
        logging.error(f"Error {resp.data['status_code']}: {resp.data['message']}")
        
    self.request_queue.clear()
      
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    if not self.connected:
      return None
    
    msg = self.request_to_message('await_request', req)
    
    resp = await self.send_message(msg, self.timeout)
    
    if not resp:
      return None
    
    if resp.data['status_code'] >= 400:
      logging.error(f"Error {resp.data['status_code']}: {resp.data['message']}")
      return None
    else:
      try:
        resp = await asyncio.wait_for(self.await_response(msg.id), 5.0)
        statusobj = resp.data['requestStatus']
        status = simpleobsws.RequestStatus(statusobj['result'], statusobj['code'], statusobj['comment'])
        return simpleobsws.RequestResponse(resp.data['requestType'], status, resp.data['responseData'])
      except asyncio.TimeoutError:
        logging.error("Never recieved awaited request response!")
        self.connected = False
        return None
      except wsexceptions.ConnectionClosed:
        logging.error('Connection closed!')
        self.connected = False
        return None
      except:
        logging.error('Unknown error occurred when awaiting response.')
        return None
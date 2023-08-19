import conn
import simpleobsws
import typing
import logging
import asyncio
from websockets import client
from websockets import typing as wstypes
from websockets import exceptions as wsexceptions
import json
import time

class ProxiedClientConnection(conn.Connection):
  roomcode : str = ""
  proxyws : client.WebSocketClientProtocol = None
  
  def __init__(self, url : str, roomcode : str, error_handler : conn.RequestResponseHandler):
    self.url = url
    self.roomcode = roomcode
    
    super().__init__(error_handler)
    
  def request_to_json(self, msgType : str, req : simpleobsws.Request):
    content = {
      'code': self.roomcode,
      'msgType': msgType,
      'hasData': True,
      'data' : {
        'requestType': req.requestType,
        'requestData': req.requestData
      }
    }
    if req.inputVariables:
      content['data']['inputVariables'] = req.inputVariables
    if req.outputVariables:
      content['data']['outputVariables'] = req.outputVariables
    return content
  
  async def connect(self) -> bool:
    try:
      self.proxyws = await client.connect(self.url)
      
      joincontent = {
        'code': self.roomcode,
        'msgType': 'client_subscribe',
        'hasData': False
      }
      await self.proxyws.send(json.dumps(joincontent))
      
      resp = await self.proxyws.recv()
      respjson = json.loads(resp)
      if respjson['status_code'] >= 400:
        logging.error(f"Error {respjson['status_code']}: {respjson['message']}")
        return False
      
      return True
    except wsexceptions.InvalidURI:
      logging.error("Invalid URI.")
      return False
    except OSError:
      logging.error("TCP connection failed.")
      return False
    except wsexceptions.InvalidHandshake:
      logging.error("Handshake failed.")
      return False
    except asyncio.TimeoutError:
      logging.error("Handshake timed out")
      return False
    except wsexceptions.ConnectionClosed:
      logging.error("Connection closed.")
      return False
    except:
      logging.error("Unknow error encountered while connecting.")
      return False
    
    
  async def update(self) -> None:
    while True:
      try: # assume messages in buffer are responses from emitted requests
        await asyncio.wait_for(self.proxyws.recv(), 0.001)
      except:
        break
        
    for req in self.request_queue:
      content = self.request_to_json('emit_request', req)
      
      await self.proxyws.send(json.dumps(content))
      
      resp = await self.proxyws.recv()
      respjson = json.loads(resp)
      if respjson['status_code'] >= 400:
        logging.error(f"Error {respjson['status_code']}: {respjson['message']}")
        
    self.request_queue.clear()
    
  async def await_response(self, request_id : int) -> dict:
    while True:
      msg = await self.proxyws.recv()
      msgjson = json.loads(msg)
      
      if 'requestId' in msgjson:
        if int(msgjson['requestId']) == request_id:
          return msgjson
        else:
          continue
      else:
        continue
      
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    content = self.request_to_json('await_request', req)
      
    await self.proxyws.send(json.dumps(content))
    
    resp = await self.proxyws.recv()
    respjson = json.loads(resp)
    if respjson['status_code'] >= 400:
      logging.error(f"Error {respjson['status_code']}: {respjson['message']}")
      return None
    else:
      request_id = int(respjson['message'])
      
      try:
        respjson = await asyncio.wait_for(self.await_response(request_id), 5.0)
        statusobj = respjson['requestStatus']
        status = simpleobsws.RequestStatus(statusobj['result'], statusobj['code'], statusobj['comment'])
        return simpleobsws.RequestResponse(respjson['requestType'], status, respjson['responseData'])
      except asyncio.TimeoutError:
        logging.error("Never recieved awaited request response!")
        return None
      except wsexceptions.ConnectionClosed:
        logging.error('Connection closed!')
        return None
      except:
        logging.error('Unknown error occurred when awaiting response.')
        return None
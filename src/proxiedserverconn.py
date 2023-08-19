import conn
import typing
import simpleobsws
import logging
import requests
import json
import datetime as dt
import asyncio
from websockets import client
from websockets import typing as wstypes
from websockets import exceptions as wsexceptions

class ProxiedServerConnection(conn.Connection):
  obsws : simpleobsws.WebSocketClient = None
  proxyws : client.WebSocketClientProtocol = None
  
  proxy_url : str = ""
  roomcode : str = ""
  
  def __init__(self, obs_url : str, password : str, proxy_url : str, roomcode : str, error_handler : conn.RequestResponseHandler):
    self.url = obs_url
    self.proxy_url = proxy_url
    self.roomcode = roomcode
    
    self.obsws = simpleobsws.WebSocketClient(url = self.url, password = password)
    
    super().__init__(error_handler)
    
  def log_requests_response(self, resp : requests.Response, comment : str = None) -> None:
    if comment:
      logging.error(comment)
    logging.error(f"Error {resp.status_code}: {str(resp.content)}")
    
  async def connect(self) -> bool:
    connected = await self.obsws.connect()
    identified = await self.obsws.wait_until_identified()
    
    try:
      self.proxyws = await client.connect(self.proxy_url)
      
      joincontent = {
        'code': self.roomcode,
        'msgType': 'server_subscribe',
        'hasData': False
      }
      await self.proxyws.send(json.dumps(joincontent))
      
      resp = await self.proxyws.recv()
      print(resp)
      respjson = json.loads(resp)
      if respjson['status_code'] >= 400:
        logging.error(f"Error {respjson['status_code']}: {respjson['message']}")
        return False
      
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
      logging.error("Unknown error encountered while connecting.")
      return False
    
    if connected and identified:
      logging.info(f"Connected to {self.url} and room created.")
      return True
    else:
      logging.error(f"Failed to authenticate with {self.url}")
      return False
    
  def send_response(self, resp : simpleobsws.RequestResponse) -> None:
    endpoint = f"{self.proxy_url}/api/v1/response"
    
    content = {
      'roomCode': self.roomcode,
      'requestType': resp.requestType,
      'requestStatus': {
        'code': resp.requestStatus.code,
        'comment': resp.requestStatus.comment,
        'result': resp.requestStatus.result
      },
      'responseData': resp.responseData
    }
    
    postresp = requests.post(url = endpoint, json = content)
    
    if postresp.status_code != 200:
      self.log_requests_response(postresp)
    
  async def update(self):
    while True:
      try:
        msg = await asyncio.wait_for(self.proxyws.recv(), 0.01)
      except:
        break
      
      msgjson = json.loads(msg)
      
      if 'requestType' in msgjson:
        if msgjson['requestType'] == 'await':
          request_id = msgjson['requestId']
          req = simpleobsws.Request(msgjson['request']['requestType'], msgjson['request']['requestData'])
          resp = await self.obsws.call(req)
          content = {
            'msgType': 'await_response',
            'code': self.roomcode,
            'hasData': True,
            'data': {
              'requestId': request_id,
              'requestType': resp.requestType,
              'requestStatus': {
                'result': resp.requestStatus.result,
                'code': resp.requestStatus.code,
                'comment': resp.requestStatus.comment
              },
              'responseData': resp.responseData
            }
          }
          await self.proxyws.send(json.dumps(content))
        if msgjson['requestType'] == 'emit':
          req = simpleobsws.Request(msgjson['request']['requestType'], msgjson['request']['requestData'])
          await self.obsws.emit(req)
          
    
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    None
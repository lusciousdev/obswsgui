import asyncio
import logging
import uuid

import requests
import simpleobsws
from websockets import client
from websockets import exceptions as wsexceptions

from .conn import RequestResponseHandler
from .proxiedconn import ProxiedConnection, Message

logging.getLogger("websockets.client").setLevel(logging.INFO)

class ProxiedServerConnection(ProxiedConnection):
  obsws : simpleobsws.WebSocketClient = None
  proxyws : client.WebSocketClientProtocol = None
  
  proxy_url : str = ""
  roomcode : str = ""
  
  def __init__(self, obs_url : str, password : str, proxy_url : str, roomcode : str, error_handler : RequestResponseHandler):
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
      self.connected = True
      
      joincontent = {
        'code': self.roomcode,
        'msgType': 'server_subscribe',
        'hasData': False
      }
      msg = Message()
      msg.code = self.roomcode
      msg.id = uuid.uuid4().int
      msg.msg_type = "server_subscribe"
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
      self.connected = False
    except wsexceptions.InvalidHandshake:
      logging.error("Handshake failed.")
      self.connected = False
    except asyncio.TimeoutError:
      logging.error("Handshake timed out")
      self.connected = False
    except wsexceptions.ConnectionClosed:
      logging.error("Connection closed.")
      self.connected = False
    except Exception as e:
      logging.error("Unknown error encountered while connecting.")
      logging.error(e)
      self.connected = False
      
    if not self.connected:
      return self.connected
      
    if connected and identified:
      logging.info(f"Connected to {self.url} and room created.")
      self.connected = True
    else:
      logging.error(f"Failed to authenticate with {self.url}")
      self.connected = False
    
    return self.connected
    
  async def update(self):
    while True:
      try:
        rawmsg = await asyncio.wait_for(self.proxyws.recv(), 0.05)
      except wsexceptions.ConnectionClosed:
        self.connected = False
        break
      except:
        break
      
      msg = Message(rawmsg)
      
      if msg.msg_type == 'await_request':
        req = simpleobsws.Request(msg.data['requestType'], msg.data['requestData'])
        obs_resp = await self.obsws.call(req)
        
        await_resp = Message()
        await_resp.code = self.roomcode
        await_resp.id = msg.id
        await_resp.msg_type = 'await_response'
        await_resp.has_data = True
        await_resp.data = {
          'requestType': obs_resp.requestType,
          'requestStatus': {
            'result': obs_resp.requestStatus.result,
            'code': obs_resp.requestStatus.code,
            'comment': obs_resp.requestStatus.comment
          },
          'responseData': obs_resp.responseData
        }
        await self.proxyws.send(await_resp.to_data())
      if msg.msg_type == 'emit_request':
        req = simpleobsws.Request(msg.data['requestType'], msg.data['requestData'])
        await self.obsws.emit(req)
    
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    None
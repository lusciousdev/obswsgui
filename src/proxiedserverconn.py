import conn
import typing
import simpleobsws
import logging
import requests
import json
import datetime as dt

class ProxiedServerConnection(conn.Connection):
  obsws : simpleobsws.WebSocketClient = None
  
  api_url : str = ""
  roomcode : str = ""
  
  last_heartbeat = None
  heartbeat_rate = 5.0 # seconds
  
  def __init__(self, ws_url : str, password : str, api_url : str, roomcode : str, error_handler : conn.RequestResponseHandler):
    self.url = ws_url
    self.api_url = api_url
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
    
    endpoint = f"{self.api_url}/api/v1/room/create?roomCode={self.roomcode}"
    resp = requests.get(url = endpoint)
    
    if resp.status_code != 200:
      self.log_requests_response(resp, "Failed to create room.")
      return False
    
    self.last_heartbeat = dt.datetime.now()
    
    if connected and identified:
      logging.info(f"Connected to {self.url} and room created.")
      return True
    else:
      logging.error(f"Failed to authenticate with {self.url}")
      return False
    
  def get_called_request(self) -> simpleobsws.Request:
    endpoint = f"{self.api_url}/api/v1/requests/await?roomCode={self.roomcode}"
    resp = requests.get(url = endpoint)
    
    if resp.status_code == 200:
      respjson = json.loads(resp.content)
      return simpleobsws.Request(respjson['requestType'], respjson['requestData'])
    elif resp.status_code == 204:
      return None
    else:
      self.log_requests_response(resp)
      return None
  
  def get_emitted_requests(self) -> typing.List[simpleobsws.Request]:
    endpoint = f"{self.api_url}/api/v1/requests/emit?roomCode={self.roomcode}"
    resp = requests.get(url = endpoint)
    
    reqs : typing.List[simpleobsws.Request] = []
    if resp.status_code == 200:
      respcontent = json.loads(resp.content)
      for reqjson in respcontent['requests']:
        req = simpleobsws.Request(reqjson['requestType'], reqjson['requestData'])
        reqs.append(req)
      return reqs
    else:
      self.log_requests_response(resp)
      return reqs
    
  def send_response(self, resp : simpleobsws.RequestResponse) -> None:
    endpoint = f"{self.api_url}/api/v1/response"
    
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
      
  def send_heartbeat(self):
    endpoint = f"{self.api_url}/api/v1/room/heartbeat?roomCode={self.roomcode}"
    resp = requests.get(url = endpoint)
    
    if resp.status_code != 200:
      self.log_requests_response(resp)
    else:
      self.last_heartbeat = dt.datetime.now()
      
  def time_since_heartbeat(self) -> int:
    return (dt.datetime.now() - self.last_heartbeat).total_seconds()
    
  async def update(self):
    req = self.get_called_request()
    
    if req:
      resp = await self.obsws.call(req)
      self.send_response(resp)
      
    reqlist = self.get_emitted_requests()
    
    for r in reqlist:
      await self.obsws.call(r)
      
    if self.time_since_heartbeat() > self.heartbeat_rate:
      self.send_heartbeat()
    
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    None
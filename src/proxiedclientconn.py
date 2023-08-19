import conn
import simpleobsws
import typing
import logging
import requests
import json
import time

class ProxiedClientConnection(conn.Connection):
  roomcode : str = ""
  
  def __init__(self, url : str, roomcode : str, error_handler : conn.RequestResponseHandler):
    self.url = url
    self.roomcode = roomcode
    
    super().__init__(error_handler)
    
  def request_to_json(self, req : simpleobsws.Request):
    content = {
      'roomCode': self.roomcode,
      'requestType': req.requestType,
      'requestData': req.requestData
    }
    if req.inputVariables:
      content['inputVariables'] = req.inputVariables
    if req.outputVariables:
      content['outputVariables'] = req.outputVariables
    return content
  
  async def connect(self) -> bool:
    return True
    
  async def update(self) -> None:
    api_endpoint = f"{self.url}/api/v1/requests/await"
    
    for req in self.request_queue:
      content = self.request_to_json(req)
      
      resp = requests.post(url = api_endpoint, json = content)
      
      if resp.status_code >= 400:
        logging.error(resp.content)
    self.request_queue.clear()
      
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    api_endpoint = f"{self.url}/api/v1/requests/await"
    
    content = self.request_to_json(req)
    
    resp = requests.post(url = api_endpoint, json = content)
    
    if resp.status_code == 200:
      try:
        respjson = json.loads(resp.content)
        statusobj = respjson['requestStatus']
        status = simpleobsws.RequestStatus(statusobj['result'], statusobj['code'], statusobj['comment'])
        return simpleobsws.RequestResponse(respjson['requestType'], status, respjson['responseData'])
      except:
        logging.error("Failed to convert API response into request response.")
        return None
    else:
      logging.error(resp.content)
      return None
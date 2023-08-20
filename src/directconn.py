import conn
import simpleobsws
import typing
import logging

class DirectConnection(conn.Connection):
  obsws : simpleobsws.WebSocketClient = None
  
  def __init__(self, url : str, password : str, error_handler : conn.RequestResponseHandler):
    self.url = url
    self.obsws = simpleobsws.WebSocketClient(url = self.url, password = password)
    
    super().__init__(error_handler)
    
  async def update(self) -> None:
    for req in self.request_queue:
      resp = await self.obsws.call(req)
      
      if not resp.ok():
        self.error_handler(resp)
        
    self.request_queue.clear()
        
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    resp = await self.obsws.call(req)
    
    if not resp.ok():
      self.error_handler(resp)
      return None
    
    return resp
    
  async def connect(self) -> bool:
    connected = await self.obsws.connect()
    identified = await self.obsws.wait_until_identified()
    
    if connected and identified:
      logging.info(f"Connected to {self.url}")
      self.connected = True
      return self.connected
    else:
      logging.error(f"Failed to authenticate with {self.url}")
      self.connected = False
      return self.connected
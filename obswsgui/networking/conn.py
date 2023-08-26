import typing
import simpleobsws

RequestResponseHandler = typing.Callable[[simpleobsws.RequestResponse], None]

class Connection:
  url : str = ""
  
  request_queue : typing.List[simpleobsws.Request] = []
  
  error_handler : RequestResponseHandler = None
  unknown_handler : RequestResponseHandler = None
  
  connected : bool = False
  
  def __init__(self, error_handler : RequestResponseHandler):
    self.error_handler = error_handler
    
  def queue_request(self, request : simpleobsws.Request) -> None:
    self.request_queue.append(request)
  
  async def request(self, req : simpleobsws.Request) -> simpleobsws.RequestResponse:
    None
    
  async def update(self) -> None:
    None
    
  async def connect(self) -> None:
    None
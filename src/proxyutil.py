import json
import logging

from websockets import exceptions as wsexceptions
from websockets import server
from websockets import typing as wstypes


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
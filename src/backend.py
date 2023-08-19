import argparse
import threading
import time
import typing
import datetime as dt

import flask
import simpleobsws
from flask_cors import CORS, cross_origin

import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def json_to_request_response(jsondata : dict) -> simpleobsws.RequestResponse:
  return simpleobsws.RequestResponse(jsondata['requestType'], jsondata['requestStatus'], jsondata['responseData'])
    
def request_response_to_json(resp : simpleobsws.RequestResponse) -> dict:
  return { 'requestType': resp.requestType, 'requestStatus': resp.requestStatus, 'responseData': resp.responseData}

def json_to_request(jsondata : dict) -> simpleobsws.Request:
  return simpleobsws.Request(jsondata['requestType'], jsondata['requestData'])

def request_to_json(req : simpleobsws.Request) -> dict:
  return { 'requestType': req.requestType, 'requestData': req.requestData }

class RoomRequests:
  expiration_time = 30.0 # seconds
  emitted_requests : typing.List[simpleobsws.Request] = []
  emitted_requests_lock : threading.Lock = threading.Lock()
  called_request : simpleobsws.Request = None
  called_response : simpleobsws.RequestResponse = None
  called_request_lock : threading.Lock = threading.Lock()
  last_heartbeat : dt.datetime = None
  
  def is_alive(self) -> bool:
    time_since_hb = dt.datetime.now() - self.last_heartbeat
    
    return (time_since_hb.total_seconds() < self.expiration_time)

class API_DataStore:
  ROOM_LIST : typing.Dict[str, RoomRequests] = {}
  
data : API_DataStore = API_DataStore()

app = flask.Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = 'Content-Type'

@app.route('/', methods = ['GET'])
@cross_origin()
def home():
  return f"""<h1>OBS WebSocket Proxy API</h1>"""

@app.route('/api/v1/room/create', methods = ['GET'])
@cross_origin()
def create_room():
  if 'roomCode' in flask.request.args:
    roomCode = flask.request.args['roomCode']
    
    if roomCode not in data.ROOM_LIST:
      data.ROOM_LIST[roomCode] = RoomRequests()
      data.ROOM_LIST[roomCode].last_heartbeat = dt.datetime.now()
      
      return "Success.", 200
    else:
      if not data.ROOM_LIST[roomCode].is_alive():
        data.ROOM_LIST[roomCode].last_heartbeat = dt.datetime.now()
        return "Room renewed.", 200
      
      return "Room code already exists.", 401
  else:
    return "Missing room code.", 401
  
@app.route('/api/v1/room/heartbeat', methods = ['GET'])
@cross_origin()
def heatbeat_room():
  if 'roomCode' in flask.request.args:
    roomCode = flask.request.args['roomCode']
    
    if roomCode in data.ROOM_LIST:
      if not data.ROOM_LIST[roomCode].is_alive():
        data.ROOM_LIST.pop(roomCode)
        return "Room code expired.", 400
      
      data.ROOM_LIST[roomCode].last_heartbeat = dt.datetime.now()
      
      return "Success.", 200
    else:
      return "Room code does not exist. Potentially expired.", 400
  else:
    return "Missing room code", 401

@app.route('/api/v1/requests/await', methods = ['GET', 'POST'])
@cross_origin()
def await_request():
  if flask.request.method == 'POST':
    if flask.request.is_json:
      reqdata = flask.request.json
      try:
        roomCode = reqdata['roomCode']
        
        if roomCode in data.ROOM_LIST:
          if not data.ROOM_LIST[roomCode].is_alive():
            data.ROOM_LIST.pop(roomCode)
            return "Room code expired.", 400
          
          with data.ROOM_LIST[roomCode].called_request_lock:
            data.ROOM_LIST[roomCode].called_request = json_to_request(reqdata)
            
            start_time = time.time()
            while not data.ROOM_LIST[roomCode].called_response:
              if (time.time() - start_time) > 10.0:
                return "Request timed out.", 400
              
            resp = data.ROOM_LIST[roomCode].called_response
            content = request_response_to_json(resp)
            data.ROOM_LIST[roomCode].called_response = None
            
            return content, 200
        else:
          return "Invalid room code.", 401
      except:
        return "Missing or invalid data.", 400
    else:
      return "POST content must be json.", 400
  elif flask.request.method == "GET":
    if 'roomCode' in flask.request.args:
      roomCode = flask.request.args['roomCode']
      
      if roomCode in data.ROOM_LIST:
        if data.ROOM_LIST[roomCode].called_request:
          req = data.ROOM_LIST[roomCode].called_request
          content = request_to_json(req)
          data.ROOM_LIST[roomCode].called_request = None
        else:
          return "No request pending.", 204
        
        return content, 200
      else:
        return "Invalid room code.", 401
    else:
      return "Missing room code.", 401
    
@app.route('/api/v1/requests/emit', methods = ['GET', 'POST'])
@cross_origin()
def emit_request():
  if flask.request.method == 'POST':
    if flask.request.is_json:
      reqdata = flask.request.json
      try:
        roomCode = reqdata['roomCode']
        
        if roomCode in data.ROOM_LIST:
          if not data.ROOM_LIST[roomCode].is_alive():
            data.ROOM_LIST.pop(roomCode)
            return "Room code expired.", 400
          
          req = json_to_request(reqdata)
          
          with data.ROOM_LIST[roomCode].emitted_requests_lock:
            data.ROOM_LIST[roomCode].emitted_requests.append(req)
          
          return "Success.", 200
        else:
          return "Invalid room code.", 401
      except:
        return "Missing or invalid data.", 400
    else:
      return "POST content must be json", 400
  elif flask.request.method == "GET":
    if 'roomCode' in flask.request.args:
      roomCode = flask.request.args['roomCode']
      
      resp = { "requests": [] }
      
      if roomCode in data.ROOM_LIST:
        if not data.ROOM_LIST[roomCode].is_alive():
          data.ROOM_LIST.pop(roomCode)
          return "Room code expired.", 400
        
        with data.ROOM_LIST[roomCode].emitted_requests_lock:
          for req in data.ROOM_LIST[roomCode].emitted_requests:
            reqjson = request_to_json(req)
            resp['requests'].append(reqjson)
          data.ROOM_LIST[roomCode].emitted_requests.clear()
        return resp, 200
      else:
        return "Invalid room code.", 401
    else:
      return 'Missing room code.', 401
    
@app.route('/api/v1/response', methods = ['POST'])
@cross_origin()
def post_response():
  if flask.request.is_json:
    try:
      reqdata = flask.request.json
      roomCode = reqdata['roomCode']
      
      resp = json_to_request_response(reqdata)
      
      if roomCode in data.ROOM_LIST:
        if not data.ROOM_LIST[roomCode].is_alive():
          data.ROOM_LIST.pop(roomCode)
          return "Room code expired.", 400
        
        data.ROOM_LIST[roomCode].called_response = resp
        
        return "Success", 200
      else:
        return "Invalid room code.", 401
    except:
      return "Missing or invalid data.", 400
  else:
    return "POST content must be json.", 400
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', '-i', default="127.0.0.1", help="API Host IP")
  parser.add_argument('--port', '-p', type=int, default=8080, help="API Port")
  
  args = parser.parse_args()
  
  app.run(host = args.host, port = args.port, debug = False, threaded = True)
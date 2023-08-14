import logging
logging.basicConfig(level = logging.INFO)

import asyncio
import time

from tkinter import *
from tkinter import ttk, font

import simpleobsws

from obs_object import *
from outputbounds import *
from textinput import *
from imageinput import *

class OBS_WS_GUI:
  ready_to_connect = False
  connected = False
  ws = None
  requests_queue = []
  
  framerate = 20
  
  video_width = 1920
  video_height = 1080
  
  platform = ""
  canvas = None
  screen = None
  current_scene = ""
  scene_items = []
  prev_selected_item = None
  
  lastpos = Coords()
  
  manip_mode = None
  
  modifyframe = None
  
  defaultfontopt = { 'font': ("Helvetica",  9) }
  largefontopt   = { 'font': ("Helvetica", 16) }
  hugefontopt    = { 'font': ("Helvetica", 24) }
  
  background_color  = "#0e0e10"
  background_medium = "#18181b"
  background_light  = "#1f1f23"
  background_button = "#2e2e35"
  text_color        = "#efeff1"
  accent_color      = "#fab4ff"
  
  style = None
  
  input_types = ["image", "text"]
  
  def __init__(self, root : Tk):
    self.root = root
    
    self.root.title("OBS WebSocket GUI")
    self.root.geometry("720x400")
    self.root.minsize(320, 180)
    self.root.configure(background = self.background_color)
    
    self.root.columnconfigure(0, weight = 1)
    self.root.rowconfigure(0, weight = 1)
    
    self.ip_addr_strvar = StringVar(self.root, value = "127.0.0.1")
    self.port_strvar = StringVar(self.root, "4455")
    self.pw_strvar = StringVar(self.root, "testpw")
    self.conn_submit_strvar = StringVar(self.root, "Connect")
    
    self.new_input_type_strvar = StringVar(self.root, "image")
    self.new_input_name_strvar = StringVar(self.root, "")
    
    self.new_image_url_strvar = StringVar(self.root, "")
    self.new_text_text_strvar = StringVar(self.root, "")
    
    self.style = ttk.Style(self.root)
    self.style.theme_create("obswsgui", parent = "alt", settings = {
      ".": {
        "configure": {
          "background": self.background_color,
          "foreground": self.text_color
        }
      },
      "TButton": {
        "configure": {
          "anchor": "center",
          "background": self.background_light,
        },
        "map": {
          "background": [('active', self.background_button)]
        }
      },
      "TEntry": {
        "configure": {
          "background": self.text_color,
          "foreground": self.background_color
        }
      },
      "TMenubutton": {
        "configure": {
          "background": self.background_button,
          "foreground": self.text_color
        }
      },
      "Large.TLabel": {
        "configure": self.largefontopt
      },
      "Large.TButton": {
        "configure": self.largefontopt
      },
      "Large.TMenubutton": {
        "configure": self.largefontopt
      },
      "Huge.TLabel": {
        "configure": self.hugefontopt
      },
      "Huge.TButton": {
        "configure": self.hugefontopt
      }
    })
    self.style.theme_use("obswsgui")
    
    self.setup_connection_ui()
    
  def start_async_loop(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
      start = time.time()
      
      self.update_modify_ui()
      self.queue_item_transform_requests()
      loop.run_until_complete(self.async_update())
      
      waittime = (1.0 / self.framerate) - (time.time() - start)
      if waittime > 0:
        time.sleep(waittime)
    
  async def async_update(self):
    if not self.connected and self.ready_to_connect:
      success = await self.attempt_connection()
      if success:
        self.set_conn_ui_state(True, "Connected.")
        self.clear_root()
        self.setup_default_ui()
      else:
        self.set_conn_ui_state(False, "Failed to connect. Retry?")
    if self.connected:      
      await self.send_requests()
      await self.get_scene_state()
    
  def clear_root(self):
    for ele in self.root.winfo_children():
      ele.destroy()
    
  def setup_connection_ui(self):
    self.connframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.connframe.place(relx = 0.5, rely = 0.5, anchor = CENTER)
    
    self.ip_addr_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.ip_addr_frame.grid(column = 0, row = 0, sticky = (N, W, E))
    
    self.ip_addr_label = ttk.Label(self.ip_addr_frame, text = "IP Address/URL", style="Large.TLabel")
    self.ip_addr_label.grid(column = 0, row = 0, sticky = W)
    self.port_label = ttk.Label(self.ip_addr_frame, text = "Port", style="Large.TLabel")
    self.port_label.grid(column = 1, row = 0, sticky = W)
    
    self.ip_addr_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.ip_addr_strvar, width = 25, **self.largefontopt)
    self.ip_addr_entry.grid(column = 0, row = 1, sticky = (W, E))
    self.port_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.port_strvar, width = 8, **self.largefontopt)
    self.port_entry.grid(column = 1, row = 1, sticky = (W, E))
    
    self.pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.pw_frame.grid(column = 0, row = 1, sticky = (S, W, E))
    self.pw_frame.grid_columnconfigure(1, weight = 1)
    
    self.pw_label = ttk.Label(self.pw_frame, text = "Password: ", style="Large.TLabel")
    self.pw_label.grid(column = 0, row = 0)
    self.pw_entry = ttk.Entry(self.pw_frame, textvariable = self.pw_strvar, **self.largefontopt)
    self.pw_entry.grid(column = 1, row = 0, sticky = (W, E))
    
    self.conn_submit = ttk.Button(self.connframe, textvariable = self.conn_submit_strvar, command = self.start_connection_attempt, style="Large.TButton")
    self.conn_submit.grid(column = 0, row = 2, sticky = (W, E))
    
  def canvas_to_scene(self, coords : Coords):
    scene_coords = Coords()
    scene_coords.x = round((coords.x - self.screen.polygon.point(0).x) / self.screen.scale)
    scene_coords.y = round((coords.y - self.screen.polygon.point(0).y) / self.screen.scale)
    return scene_coords
  
  def update_lastpos(self, x, y):
    self.lastpos.x = x
    self.lastpos.y = y
    
  def get_items_under_mouse(self, coords : Coords):
    items_under = []
    
    for item in self.scene_items:
      manip_mode = item.move_or_resize(coords)
      if manip_mode != ModifyType.NONE:
        items_under.append((item, manip_mode))
        
    return items_under

  def mouseDown(self, event):
    self.update_lastpos(event.x, event.y)
    
    items_under = self.get_items_under_mouse(self.lastpos)
    
    for item in self.scene_items:
      if item.selected:
        in_under = False
        for under_item in items_under:
          if item.scene_item_id == under_item[0].scene_item_id:
            in_under = True
            break
        item.set_selected(in_under)
    
    already_focused = False
    for item in items_under:
      if item[0].selected:
        already_focused = True
        self.manip_mode = item[1]
    if not already_focused and len(items_under) > 0:
      self.manip_mode = items_under[0][1]
      items_under[0][0].set_selected(True)
      items_under[0][0].setup_modify_ui(self)
          
  def doubleClick(self, event):
    self.update_lastpos(event.x, event.y)
    
    scene_coords = self.canvas_to_scene(self.lastpos)
    
    items_under = self.get_items_under_mouse(scene_coords)
    
    for item in self.scene_items:
      if item.selected:
        in_under = False
        for under_item in items_under:
          if item.scene_item_id == under_item[0].scene_item_id:
            in_under = True
            break
        item.set_selected(in_under)
    
    already_focused = False
    for i in range(0, len(items_under)):
      if items_under[i][0].selected:
        already_focused = True
        if len(items_under) > (i + 1):
          items_under[i][0].set_selected(False)
          items_under[i + 1][0].set_selected(True)
          self.manip_mode = items_under[i+1][1]
          items_under[i + 1][0].setup_modify_ui(self)
        if i > 0 and i == len(items_under) - 1:
          items_under[i][0].set_selected(False)
          items_under[0][0].set_selected(True)
          self.manip_mode = items_under[0][1]
          items_under[0][0].setup_modify_ui(self)
        break
    if not already_focused and len(items_under) > 0:
      self.manip_mode = items_under[0][1]
      items_under[0][0].set_selected(True)
      items_under[0][0].setup_modify_ui(self)

  def mouseMove(self, event):
    diffX = round((event.x - self.lastpos.x) / self.screen.scale)
    diffY = round((event.y - self.lastpos.y) / self.screen.scale)
    for item in self.scene_items:
      if item.selected:
        if self.manip_mode == ModifyType.MOVE:
          x = item.x + diffX
          y = item.y + diffY
          item.set_transform(x = x, y = y)
        elif self.manip_mode == ModifyType.ROTATE:
          center = item.polygon.centroid()
          v1 = self.lastpos - center
          v2 = Coords(event.x, event.y) - center
          
          a1 = v1.angle()
          a2 = v2.angle()
          adelta = a2 - a1
          
          normalized_center = (center - item.polygon.point(0)) / self.screen.scale
          
          rotated_center = normalized_center.__copy__()
          rotated_center.rotate(adelta)
          
          displacement = rotated_center - normalized_center
          
          new_rot = item.rotation + adelta
          new_x = item.x - displacement.x
          new_y = item.y - displacement.y
          
          item.set_transform(x = new_x, y = new_y, rot = new_rot)
        else:
          x = item.x
          y = item.y
          w = item.width
          h = item.height
          
          moveangle = Coords(diffX, diffY).angle()
          aprime = moveangle - item.rotation
          movedist = math.sqrt(math.pow(diffX, 2) + math.pow(diffY, 2))
          rotatedX = movedist * math.cos(aprime)
          rotatedY = movedist * math.sin(aprime)
          
          if (self.manip_mode & ModifyType.LEFT != 0):
            corrX = rotatedX * math.cos(item.rotation)
            corrY = rotatedX * math.sin(item.rotation)
            x += corrX
            y += corrY
          
          if (self.manip_mode & ModifyType.TOP != 0):
            corrX = rotatedY * math.cos((math.pi / 2) - item.rotation)
            corrY = rotatedY * math.sin((math.pi / 2) - item.rotation)
            x -= corrX
            y += corrY
          
          if self.manip_mode & ModifyType.LEFT != 0:
            w -= rotatedX
          if self.manip_mode & ModifyType.RIGHT != 0:
            w += rotatedX
          if self.manip_mode & ModifyType.TOP != 0:
            h -= rotatedY
          if self.manip_mode & ModifyType.BOTTOM != 0:
            h += rotatedY
            
          item.set_transform(x, y, w, h)
        
    self.update_lastpos(event.x, event.y)
    
  def mouseUp(self, event):
    return
  
  def get_selected_item(self):
    for item in self.scene_items:
      if item.selected:
        return item
    return None
      
  def clear_canvas(self):
    self.canvas.delete("all")
    
  def canvas_configure(self, event = None):
    if self.canvas:
      if self.screen:
        self.screen.canvas_configure(event)
      
      for item in self.scene_items:
        item.canvas_configure(event)
        
  def queue_set_item_transform(self, item : OBS_Object):
    scale_x = 1.0 if item.source_width == 0.0 else item.width / item.source_width
    scale_y = 1.0 if item.source_height == 0.0 else item.height / item.source_height
    rot = (180.0 * item.rotation / math.pi) % 360.0
    if item.bounds_type == 'OBS_BOUNDS_SCALE_INNER':
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': self.current_scene, 'sceneItemId': item.scene_item_id, 'sceneItemTransform': { 'positionX': item.x, 'positionY': item.y, 'boundsWidth': item.width, 'boundsHeight': item.height, 'rotation': rot }})
    else:
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': self.current_scene, 'sceneItemId': item.scene_item_id, 'sceneItemTransform': { 'positionX': item.x, 'positionY': item.y, 'scaleX': scale_x, 'scaleY': scale_y, 'rotation': rot }})
      
    self.requests_queue.append(tf_req)
    
  def setup_default_ui(self):
    self.defaultframe = ttk.Frame(self.root, padding = "5 5 5 5")
    self.defaultframe.pack(anchor = CENTER, fill = BOTH, expand = True)
    self.defaultframe.columnconfigure(0, minsize=150)
    self.defaultframe.columnconfigure(1, weight = 1)
    self.defaultframe.rowconfigure(0, weight=1)
    
    self.modifyframe = ttk.Frame(self.defaultframe, padding="0 0 5 5")
    self.modifyframe.grid(column = 0, row = 0, sticky = (N, W, E, S))
    
    self.canvas = Canvas(self.defaultframe, background = self.background_light, bd = 0, highlightthickness = 0, relief = 'ridge')
    self.canvas.grid(column = 1, row = 0, sticky = (N, W, E, S), padx = (5, 0), pady = (0, 5))
        
    self.canvas.bind("<Configure>", self.canvas_configure)
    self.canvas.bind("<Button-1>", self.mouseDown)
    self.canvas.bind("<Double-Button-1>", self.doubleClick)
    self.canvas.bind("<ButtonRelease-1>", self.mouseUp)
    self.canvas.bind("<B1-Motion>", self.mouseMove)
    
    self.addimage = ttk.Button(self.defaultframe, text = "+", command = self.setup_add_input_dialog, width = 14, style = "Large.TButton")
    self.addimage.grid(column = 1, row = 1, sticky = W, padx = (5, 0))
    
    self.screen = OutputBounds(self.canvas, anchor = CENTER, width = self.video_width, height = self.video_height, label = "Output")
    
    self.canvas_configure()
    
  def setup_add_image_dialog(self):
    self.new_image_name_label = ttk.Label(self.add_input_settings_frame, text = "Input name", style = "Large.TLabel")
    self.new_image_name_label.grid(column = 0, row = 0, sticky = W)
    self.new_image_name_entry = ttk.Entry(self.add_input_settings_frame, textvariable = self.new_input_name_strvar, width = 48, **self.largefontopt)
    self.new_image_name_entry.grid(column = 0, row = 1, sticky = W, pady = (0, 10))
    
    self.new_image_url_label = ttk.Label(self.add_input_settings_frame, text = "Image URL (must be online)", style = "Large.TLabel")
    self.new_image_url_label.grid(column = 0, row = 2, sticky = W)
    self.new_image_url_entry = ttk.Entry(self.add_input_settings_frame, textvariable = self.new_image_url_strvar, width = 48, **self.largefontopt)
    self.new_image_url_entry.grid(column = 0, row = 3, sticky = W, pady = (0, 10))
    
    self.add_image_button_frame = ttk.Frame(self.add_input_settings_frame)
    self.add_image_button_frame.grid(column = 0, row = 5, sticky=E)
    
    def addimg():
      self.queue_add_image_req()
      self.close_add_input_dialog()
    
    self.new_image_submit = ttk.Button(self.add_image_button_frame, text = "Add", command = addimg, padding = "5 0 0 0", style = "Large.TButton")
    self.new_image_submit.grid(column = 0, row = 0, sticky = E, padx = (5, 5))
  
    self.new_image_cancel = ttk.Button(self.add_image_button_frame, text = "Cancel", command = self.close_add_input_dialog, style="Large.TButton")
    self.new_image_cancel.grid(column = 1, row = 0, sticky = E, padx = (5, 5))
    
  def setup_add_text_dialog(self):
    self.new_text_name_label = ttk.Label(self.add_input_settings_frame, text = "Input name", style = "Large.TLabel")
    self.new_text_name_label.grid(column = 0, row = 0, sticky = W)
    self.new_text_name_entry = ttk.Entry(self.add_input_settings_frame, textvariable = self.new_input_name_strvar, width = 48, **self.largefontopt)
    self.new_text_name_entry.grid(column = 0, row = 1, sticky = W, pady = (0, 10))
    
    self.new_text_url_label = ttk.Label(self.add_input_settings_frame, text = "Text", style = "Large.TLabel")
    self.new_text_url_label.grid(column = 0, row = 2, sticky = W)
    self.new_text_url_entry = ttk.Entry(self.add_input_settings_frame, textvariable = self.new_text_text_strvar, width = 48, **self.largefontopt)
    self.new_text_url_entry.grid(column = 0, row = 3, sticky = W, pady = (0, 10))
    
    self.add_text_button_frame = ttk.Frame(self.add_input_settings_frame)
    self.add_text_button_frame.grid(column = 0, row = 5, sticky=E)
    
    def addimg():
      self.queue_add_text_req()
      self.close_add_input_dialog()
    
    self.new_image_submit = ttk.Button(self.add_text_button_frame, text = "Add", command = addimg, padding = "5 0 0 0", style = "Large.TButton")
    self.new_image_submit.grid(column = 0, row = 0, sticky = E, padx = (5, 5))
  
    self.new_image_cancel = ttk.Button(self.add_text_button_frame, text = "Cancel", command = self.close_add_input_dialog, style="Large.TButton")
    self.new_image_cancel.grid(column = 1, row = 0, sticky = E, padx = (5, 5))
    
  def close_add_input_dialog(self):
    self.new_input_name_strvar.set("")
    self.new_image_url_strvar.set("")
    self.new_text_text_strvar.set("")
    self.add_input_dialog.destroy()
  
  def setup_add_input_dialog(self):
    x = self.root.winfo_x()
    y = self.root.winfo_y()
    
    self.add_input_dialog = Toplevel(self.root, background = self.background_color)
    self.add_input_dialog.geometry(f"+{x + 10}+{y + 50}")
    self.add_input_dialog.minsize(200, 100)
    self.add_input_dialog.columnconfigure(0, weight = 1)
    
    self.add_input_dialog.protocol("WM_DELETE_WINDOW", self.close_add_input_dialog)
    
    self.add_input_type_frame = ttk.Frame(self.add_input_dialog, padding = "5 5 5 5")
    self.add_input_type_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.add_input_type_frame.grid_columnconfigure(0, weight = 1)
    
    self.add_input_type_label = ttk.Label(self.add_input_type_frame, text = "Input type", style = "Large.TLabel")
    self.add_input_type_label.grid(column = 0, row = 0, sticky = W)
    self.add_input_type_select = ttk.OptionMenu(self.add_input_type_frame, self.new_input_type_strvar, self.input_types[0], *self.input_types, command = self.new_input_type_change, style = "Large.TMenubutton")
    self.add_input_type_select.grid(column = 0, row = 1, sticky = (W, E))
    
    self.add_input_settings_frame = ttk.Frame(self.add_input_dialog, padding = "5 5 5 5")
    self.add_input_settings_frame.grid(column = 0, row = 1, sticky = (N, W, E, S))
    self.add_input_settings_frame.grid_columnconfigure(0, weight = 1)
    
    self.new_input_type_change()
    
  def new_input_type_change(self, *args):
    inputtype = self.new_input_type_strvar.get()
    
    # clear the input settings frame
    for item in self.add_input_settings_frame.winfo_children():
      item.destroy()
    
    if inputtype == "image":
      self.setup_add_image_dialog()
    elif inputtype == "text":
      self.setup_add_text_dialog()
    
  def queue_add_image_req(self):
    img_name = self.new_input_name_strvar.get()
    img_url  = self.new_image_url_strvar.get()
    
    if img_name != "" and img_url != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': self.current_scene, 'inputName': img_name, 'inputKind': 'image_source', 'inputSettings': { 'file': img_url }, 'sceneItemEnabled': True })
      self.requests_queue.append(img_req)
    
  def queue_add_text_req(self):
    input_name = self.new_input_name_strvar.get()
    input_text = self.new_text_text_strvar.get()
    input_kind = 'text_gdiplus_v2' if self.platform == "windows" else 'text_ft2_source_v2'
    
    if input_name != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': self.current_scene, 'inputName': input_name, 'inputKind': input_kind, 'inputSettings': { 'text': input_text }, 'sceneItemEnabled': True })
      self.requests_queue.append(img_req)
  
  def set_conn_ui_state(self, disabled : bool, submit_str : str):
    self.conn_submit_strvar.set(submit_str)
    state = 'disable' if disabled else 'enable'
    self.ip_addr_entry['state'] = state
    self.port_entry['state'] = state
    self.pw_entry['state'] = state
    self.conn_submit['state'] = state
    
  def start_connection_attempt(self):
    self.set_conn_ui_state(True, "Attempting connection...")
    self.ready_to_connect = True
    
  def clear_modify_ui(self):
    if self.modifyframe:
      for item in self.modifyframe.winfo_children():
        item.destroy()
    
  def update_modify_ui(self):
    selected_item = self.get_selected_item()
    if self.modifyframe and (not selected_item or (self.prev_selected_item != selected_item)):
      self.prev_selected_item = selected_item
      self.clear_modify_ui()
      if selected_item:
        selected_item.setup_modify_ui(self)
    
  async def attempt_connection(self):
    self.ready_to_connect = False
      
    ip_addr = self.ip_addr_strvar.get()
    port = self.port_strvar.get()
    password = self.pw_strvar.get()
    
    self.conn_submit_strvar.set("Attempting to connect...")
    
    self.ws = simpleobsws.WebSocketClient(url = f"ws://{ip_addr}:{port}", password = password)
    
    connected = await self.ws.connect()
    identified = await self.ws.wait_until_identified()
    
    if connected and identified:
      self.connected = True
      logging.info("Connected and identified.")
    else:
      self.connected = False
      logging.error("Failed to connect or identify.")
      return False
    
    req = simpleobsws.Request('GetVersion')
    ret = await self.ws.call(req)
    
    if not ret.ok():
      self.log_request_error(ret)
      self.connected = False
      return False

    self.platform = ret.responseData['platform']
    
    screenw, screenh = await self.get_video_settings()
    
    if not screenw or not screenh:
      return False
    else:
      self.video_width = screenw
      self.video_height = screenh
      return True
  
  async def get_video_settings(self):
    req = simpleobsws.Request('GetVideoSettings')
    ret = await self.ws.call(req)
    
    if not ret.ok():
      self.log_request_error(ret)
      self.connected = False
      return None, None
  
    return ret.responseData["baseWidth"], ret.responseData["baseHeight"]
  
  def find_scene_item(self, item_id):
    for item in self.scene_items:
      if (item.scene_item_id == item_id):
        return item
    return None
  
  async def get_image_for_item(self, item):
    req = simpleobsws.Request('GetInputSettings', { 'inputName': item.source_name })
    ret = await self.ws.call(req)
    
    if not ret.ok():
      self.log_request_error(ret)
    elif 'file' in ret.responseData['inputSettings']:
      url = ret.responseData['inputSettings']['file']
      item.set_image_url(url)
  
  async def get_text_settings(self, item):
    req = simpleobsws.Request('GetInputSettings', { 'inputName': item.source_name })
    ret = await self.ws.call(req)
    
    if not ret.ok():
      self.log_request_error(ret)
    else:
      if 'text' in ret.responseData['inputSettings']:
        text = ret.responseData['inputSettings']['text']
        item.set_text(text)
      if 'vertical' in ret.responseData['inputSettings']:
        vertical = ret.responseData['inputSettings']['vertical']
        item.set_vertical(vertical)
  
  async def get_scene_state(self):
    req = simpleobsws.Request('GetCurrentProgramScene')
    ret = await self.ws.call(req)
    
    if not ret.ok():
      logging.error("Failed to get current scene.")
      return False
    
    active_scene = ret.responseData["currentProgramSceneName"]
    if self.current_scene != active_scene:
      self.current_scene = active_scene
      for item in self.scene_items[:]:
        item.remove_from_canvas()
        self.scene_items.remove(item)
    
    screenw, screenh = await self.get_video_settings()
    if screenw and screenh:
      if self.video_height != screenh or self.video_width != screenw:
        self.video_width = screenw
        self.video_height = screenh
        self.screen.set_transform(w = self.video_width, h = self.video_height)
        self.canvas_configure()
    
    req = simpleobsws.Request('GetSceneItemList', { 'sceneName' : self.current_scene })
    ret = await self.ws.call(req)
    
    if not ret.ok():
      logging.error("Failed to get scene items")
    
    item_list = ret.responseData['sceneItems']
    
    for saved in self.scene_items[:]:
      found = False
      for active in item_list:
        if saved.scene_item_id == active['sceneItemId']:
          found = True
          break
      if not found:
        saved.remove_from_canvas()
        self.scene_items.remove(saved)
        
    for i in item_list:
      item = self.find_scene_item(i['sceneItemId'])
      tf = i['sceneItemTransform']
      
      # print(tf)
      # print(f"X: {tf['positionX']} Y: {tf['positionY']} W: {tf['width']} H: {tf['height']} BW: {tf['boundsWidth']} BH: {tf['boundsHeight']} SX: {tf['scaleX']} SY: {tf['scaleY']} CL: {tf['cropLeft']} CR: {tf['cropRight']}")
      
      x = tf['positionX']
      y = tf['positionY']
      
      w = tf['width']
      h = tf['height']
      
      a = tf['rotation']
      
      sw = tf['sourceWidth']
      sh = tf['sourceHeight']
      
      if tf['boundsType'] == 'OBS_BOUNDS_SCALE_INNER':
        w = tf['boundsWidth']
        h = tf['boundsHeight']
      
      if item:
        item.set_transform(x, y, w, h, (math.pi * a / 180.0), local = False)
        item.set_source_name(i['sourceName'])
        item.source_width = sw
        item.source_height = sh
        item.bounds_type = tf['boundsType']
        item.scene_item_index = i['sceneItemIndex']
        
        if i['inputKind'] == 'image_source':
          await self.get_image_for_item(item)
        if i['inputKind'] == 'text_gdiplus_v2' or i['inputKind'] == 'text_ft2_source_v2':
          await self.get_text_settings(item)
        
      else:
        if i['inputKind'] == 'image_source':
          item = ImageInput(i['sceneItemId'], i['sceneItemIndex'], self.canvas, self.screen, x, y, w, h, a, sw, sh, tf['boundsType'], i['sourceName'])
          await self.get_image_for_item(item)
        elif i['inputKind'] == 'text_gdiplus_v2' or i['inputKind'] == 'text_ft2_source_v2':
          item = TextInput(i['sceneItemId'], i['sceneItemIndex'], self.canvas, self.screen, x, y, w, h, a, sw, sh, tf['boundsType'], i['sourceName'])
          await self.get_text_settings(item)
        else:
          item = OBS_Object(i['sceneItemId'], i['sceneItemIndex'], self.canvas, self.screen, x, y, w, h, a, sw, sh, tf['boundsType'], i['sourceName'])
          item.set_interactable(False)
          
        self.scene_items.append(item)
            
    # sort the scene items to match the OBS source list
    self.scene_items.sort(key = lambda item: item.scene_item_index, reverse = True)
    
    for i in range(1, len(self.scene_items)):
      self.scene_items[i - 1].move_to_front(self.scene_items[i].item_label_id)
      
  def queue_item_transform_requests(self):
    for item in self.scene_items:
      if item.changed:
        self.queue_set_item_transform(item)
        item.changed = False
    
  async def send_requests(self):
    for req in self.requests_queue:
      ret = await self.ws.call(req)
      
      if not ret.ok():
        self.log_request_error(ret)
        
    self.requests_queue.clear()
    
  def log_request_error(self, ret):
    try:
      logging.error(f"Error {ret.requestStatus['code']}: {ret.requestStatus['comment']}")
    except:
      logging.error(ret)
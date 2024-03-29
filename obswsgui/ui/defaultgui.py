import logging

logging.basicConfig(level = logging.INFO)

import asyncio
import datetime as dt
import json
import math
import os
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Dict, List, Tuple

import simpleobsws

from ..networking.directconn import DirectConnection
from ..obstypes.countdowninput import TIME_FORMAT, CountdownInput
from ..obstypes.counterinput import CounterInput
from ..obstypes.imageinput import ImageInput
from ..obstypes.obs_object import ModifyType, OBS_Object
from ..obstypes.outputbounds import OutputBounds
from ..obstypes.textinput import TextInput
from ..obstypes.stopwatchinput import StopwatchInput
from ..obstypes.timerinput import TimerInput
from ..util.geometryutil import Coords
from ..util.miscutil import obs_to_color

user_types : List[OBS_Object] = [
  ImageInput,
  TextInput,
  CountdownInput,
  StopwatchInput,
  CounterInput,
  TimerInput
]

user_types_map : Dict[str, OBS_Object] = { v.description():v for v in user_types }

class Default_GUI:
  ready_to_connect : bool = False
  connected : bool = False
  
  connection : DirectConnection = None
  
  framerate : float = 20.0
  
  output_width : float  = 1920.0
  output_height : float = 1080.0
  
  platform : str = ""
  canvas : tk.Canvas = None
  screen : OutputBounds = None
  
  current_scene : str = None
  scenes : Dict[str, List[OBS_Object]] = {}
  
  prev_selected_item : OBS_Object = None
  
  lastpos : Coords = Coords()
  
  manip_mode : ModifyType = ModifyType.NONE
  
  modifyframe : ttk.Frame = None
  
  defaultfontopt : dict = { 'font': ("Helvetica",  9) }
  largefontopt   : dict = { 'font': ("Helvetica", 16) }
  hugefontopt    : dict = { 'font': ("Helvetica", 24) }
  
  background_color  : str = "#0e0e10"
  background_medium : str = "#18181b"
  background_light  : str = "#1f1f23"
  background_button : str = "#2e2e35"
  text_color        : str = "#efeff1"
  accent_color      : str = "#fab4ff"
  
  style : ttk.Style = None
  
  rotation_groove : float = 8.0 # degrees
  edge_groove     : float = 8.0 # pixels
  
  savefile = Path("./obswsguidata.json")
  
  def __init__(self, root : tk.Tk) -> None:
    self.root = root
    
    self.root.title("OBS WebSocket GUI")
    self.root.geometry("750x400")
    self.root.minsize(650, 500)
    self.root.configure(background = self.background_color)
    self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    self.root.columnconfigure(0, weight = 1)
    self.root.rowconfigure(0, weight = 1)
    
    self.addr_strvar        = tk.StringVar(self.root, value = "ws://127.0.0.1:4455")
    self.pw_strvar          = tk.StringVar(self.root, "testpw")
    self.conn_submit_strvar = tk.StringVar(self.root, "Connect")
    
    self.new_input_type_strvar = tk.StringVar(self.root, "image")
    self.new_input_name_strvar = tk.StringVar(self.root, "")
    
    self.string_param_1 = tk.StringVar(self.root, "")
    self.string_param_2 = tk.StringVar(self.root, "")
    self.string_param_3 = tk.StringVar(self.root, "")
    
    self.boolean_param_1 = tk.BooleanVar(self.root, False)
    self.int_param_1 = tk.IntVar(self.root, 0)
    self.double_param_1 = tk.DoubleVar(self.root, 0.0)
    
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
      "Large.TCheckbutton": {
        "configure": {
          **self.largefontopt,
          "indicatorcolor": self.background_button
        }
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
      self.update_items()
      self.queue_item_modification_requests()
      loop.run_until_complete(self.async_update())
      
      frametime = (time.time() - start)
      waittime = (1.0 / self.framerate) - frametime
      if waittime > 0:
        time.sleep(waittime)
        
  def update_items(self) -> None:
    for item in self.get_current_scene_items():
      item.update(self)
    
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
      await self.connection.update()
      await self.get_scene_state()
      
      if not self.connection.connected:
        self.reset_to_connection_ui()
    
  def clear_root(self) -> None:
    for ele in self.root.winfo_children():
      ele.destroy()
      
  def on_close(self) -> None:
    self.save_scene_items()
    self.root.destroy()
      
  def reset_to_connection_ui(self) -> None:
      self.connected = False
      self.ready_to_connect = False
      self.clear_root()
      self.setup_connection_ui()
      
      self.current_scene = ""
      self.scenes = {}
      self.screen = None
      self.modifyframe = None
    
    
  def setup_connection_ui(self) -> None:
    self.connframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.connframe.place(relx = 0.5, rely = 0.5, anchor = tk.CENTER)
    
    self.ip_addr_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.ip_addr_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E))
    self.ip_addr_frame.columnconfigure(0, weight = 1)
    
    self.ip_addr_label = ttk.Label(self.ip_addr_frame, text = "OBS WebSocket address", style="Large.TLabel")
    self.ip_addr_label.grid(column = 0, row = 0, sticky = tk.W)
    
    self.ip_addr_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.addr_strvar, width = 25, **self.largefontopt)
    self.ip_addr_entry.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    
    self.pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.pw_frame.grid(column = 0, row = 1, sticky = (tk.S, tk.W, tk.E))
    self.pw_frame.columnconfigure(1, weight = 1)
    
    self.pw_label = ttk.Label(self.pw_frame, text = "Password: ", style="Large.TLabel")
    self.pw_label.grid(column = 0, row = 0)
    self.pw_entry = ttk.Entry(self.pw_frame, textvariable = self.pw_strvar, **self.largefontopt)
    self.pw_entry.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    
    self.conn_submit = ttk.Button(self.connframe, textvariable = self.conn_submit_strvar, command = self.start_connection_attempt, style="Large.TButton")
    self.conn_submit.grid(column = 0, row = 2, sticky = (tk.W, tk.E))
    
  def canvas_to_scene(self, coords : Coords) -> Coords:
    scene_coords = Coords()
    scene_coords.x = round((coords.x - self.screen.polygon.point(0).x) / self.screen.scale)
    scene_coords.y = round((coords.y - self.screen.polygon.point(0).y) / self.screen.scale)
    return scene_coords
  
  def update_lastpos(self, x : float, y : float) -> None:
    self.lastpos.x = x
    self.lastpos.y = y
    
  def get_items_under_mouse(self, coords : Coords) -> List[Tuple[OBS_Object, ModifyType]]:
    items_under : List[Tuple[OBS_Object, ModifyType]] = []
    
    for item in self.get_current_scene_items():
      manip_mode = item.move_or_resize(coords)
      if manip_mode != ModifyType.NONE:
        items_under.append((item, manip_mode))
        
    return items_under

  def mouseDown(self, event : tk.Event) -> None:
    self.update_lastpos(event.x, event.y)
    
    self.xpull = 0
    self.ypull = 0
    
    items_under = self.get_items_under_mouse(self.lastpos)
    
    for item in self.get_current_scene_items():
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
          
  def doubleClick(self, event : tk.Event) -> None:
    self.update_lastpos(event.x, event.y)
    
    scene_coords = self.canvas_to_scene(self.lastpos)
    
    items_under = self.get_items_under_mouse(scene_coords)
    
    for item in self.get_current_scene_items():
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

  def mouseMove(self, event : tk.Event) -> None:
    diffX = round((event.x - self.lastpos.x) / self.screen.scale)
    diffY = round((event.y - self.lastpos.y) / self.screen.scale)
    for item in self.get_current_scene_items():
      if item.selected:
        x = item.x
        y = item.y
        w = item.width
        h = item.height
        r = item.rotation
        
        if self.manip_mode == ModifyType.MOVE:
          x += diffX
          y += diffY
          
          dist_from_right_edge = self.screen.width - (x + w)
          dist_from_bottom_edge = self.screen.height - (y + h)
              
          if abs(x) < self.edge_groove:
            if abs(self.xpull) < (2.0 * self.edge_groove):
              self.xpull += x
              x = 0
            else:
              x = self.xpull
              self.xpull = 0
          elif abs(dist_from_right_edge) < self.edge_groove:
            if abs(self.xpull) < (2.0 * self.edge_groove):
              self.xpull += dist_from_right_edge
              x = self.screen.width - w
            else:
              x = self.screen.width - w - self.xpull
              self.xpull = 0
              
          if abs(y) < self.edge_groove:
            if abs(self.ypull) < (2.0 * self.edge_groove):
              self.ypull += y
              y = 0
            else:
              y = self.ypull
              self.ypull = 0
          elif abs(dist_from_bottom_edge) < self.edge_groove:
            if abs(self.ypull) < (2.0 * self.edge_groove):
              self.ypull += dist_from_bottom_edge
              y = self.screen.height - h
            else:
              y = self.screen.height - h - self.ypull
              self.ypull = 0
          
        elif self.manip_mode == ModifyType.ROTATE:
          center = item.polygon.centroid()
          v2 = Coords(event.x, event.y) - center
          
          new_angle = v2.angle() + (math.pi / 2)
                 
          for i in range(8):
            if abs((i * math.pi / 4) - new_angle) < (0.5 * self.rotation_groove * math.pi / 180.0):
              new_angle = i * math.pi / 4
          
          adelta = new_angle - r
          
          normalized_center = (center - item.polygon.point(0)) / self.screen.scale
          
          rotated_center = normalized_center.__copy__()
          rotated_center.rotate(adelta)
          
          displacement = rotated_center - normalized_center
          
          x -= displacement.x
          y -= displacement.y
          r  = new_angle
        else:
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
            
        item.set_transform(x, y, w, h, r)
        
    self.update_lastpos(event.x, event.y)
    
  def mouseUp(self, event : tk.Event) -> None:
    return
  
  def get_current_scene_items(self) -> List[OBS_Object]:
    if self.current_scene and self.current_scene not in self.scenes:
      self.scenes[self.current_scene] = []
      return self.scenes[self.current_scene]
    elif self.current_scene:
      return self.scenes[self.current_scene]
    else:
      return []
  
  def get_selected_item(self) -> OBS_Object:
    for item in self.get_current_scene_items():
      if item.selected:
        return item
    return None
      
  def clear_canvas(self) -> None:
    self.canvas.delete("all")
    
  def canvas_configure(self, event : tk.Event = None) -> None:
    if self.canvas:
      if self.screen:
        self.screen.canvas_configure(event)
      
      for item in self.get_current_scene_items():
        item.canvas_configure(event)
    
  def setup_default_ui(self) -> None:
    self.defaultframe = ttk.Frame(self.root, padding = "5 5 5 5")
    self.defaultframe.pack(anchor = tk.CENTER, fill = tk.BOTH, expand = True)
    self.defaultframe.columnconfigure(0, minsize=175)
    self.defaultframe.columnconfigure(1, weight = 1)
    self.defaultframe.rowconfigure(0, weight=1)
    
    self.modifyframe = ttk.Frame(self.defaultframe, padding="0 0 5 5")
    self.modifyframe.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S))
    
    self.canvas = tk.Canvas(self.defaultframe, background = self.background_light, bd = 0, highlightthickness = 0, relief = 'ridge')
    self.canvas.grid(column = 1, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S), padx = (5, 0), pady = (0, 5))
        
    self.canvas.bind("<Configure>", self.canvas_configure)
    self.canvas.bind("<Button-1>", self.mouseDown)
    self.canvas.bind("<Double-Button-1>", self.doubleClick)
    self.canvas.bind("<ButtonRelease-1>", self.mouseUp)
    self.canvas.bind("<B1-Motion>", self.mouseMove)
    
    self.addimage = ttk.Button(self.defaultframe, text = "+", command = self.setup_add_input_dialog, width = 14, style = "Large.TButton")
    self.addimage.grid(column = 1, row = 1, sticky = tk.W, padx = (5, 0))
    
    self.screen = OutputBounds(self.canvas, anchor = tk.CENTER, width = self.output_width, height = self.output_height, label = "Output")
    
    self.load_scene_items()
    
    self.canvas_configure()
    
  def close_add_input_dialog(self) -> None:
    self.new_input_name_strvar.set("")
    self.string_param_1.set("")
    self.add_input_dialog.destroy()
  
  def setup_add_input_dialog(self) -> None:
    x = self.root.winfo_x()
    y = self.root.winfo_y()
    
    self.add_input_dialog = tk.Toplevel(self.root, background = self.background_color)
    self.add_input_dialog.geometry(f"+{x + 10}+{y + 50}")
    self.add_input_dialog.minsize(200, 100)
    self.add_input_dialog.columnconfigure(0, weight = 1)
    
    self.add_input_dialog.protocol("WM_DELETE_WINDOW", self.close_add_input_dialog)
    
    self.add_input_type_frame = ttk.Frame(self.add_input_dialog, padding = "5 5 5 5")
    self.add_input_type_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.add_input_type_frame.columnconfigure(0, weight = 1)
    
    self.add_input_type_label = ttk.Label(self.add_input_type_frame, text = "Input type", style = "Large.TLabel")
    self.add_input_type_label.grid(column = 0, row = 0, sticky = tk.W)
    opts = list(user_types_map.keys())
    self.add_input_type_select = ttk.OptionMenu(self.add_input_type_frame, self.new_input_type_strvar, opts[0], *opts, command = self.new_input_type_change, style = "Large.TMenubutton")
    self.add_input_type_select.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    
    self.add_input_settings_frame = ttk.Frame(self.add_input_dialog, padding = "5 5 5 5")
    self.add_input_settings_frame.grid(column = 0, row = 1, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.add_input_settings_frame.columnconfigure(0, weight = 1)
    
    self.new_input_type_change()
    
  def new_input_type_change(self, *args) -> None:
    inputtype = self.new_input_type_strvar.get()
    
    # clear the input settings frame
    for item in self.add_input_settings_frame.winfo_children():
      item.destroy()
      
    frame = self.add_input_settings_frame
    
    user_types_map[inputtype].setup_create_ui(self, frame)
  
  def set_conn_ui_state(self, disabled : bool, submit_str : str) -> None:
    self.conn_submit_strvar.set(submit_str)
    state = 'disable' if disabled else 'enable'
    self.ip_addr_entry['state'] = state
    self.pw_entry['state'] = state
    self.conn_submit['state'] = state
    
  def start_connection_attempt(self) -> None:
    self.set_conn_ui_state(True, "Attempting connection...")
    self.ready_to_connect = True
    
  def clear_modify_ui(self) -> None:
    if self.modifyframe:
      for item in self.modifyframe.winfo_children():
        item.destroy()
    
  def update_modify_ui(self) -> None:
    selected_item = self.get_selected_item()
    if self.modifyframe and (not selected_item or (self.prev_selected_item != selected_item)):
      self.prev_selected_item = selected_item
      self.clear_modify_ui()
      if selected_item:
        selected_item.setup_modify_ui(self)
    
  async def attempt_connection(self):
    self.ready_to_connect = False
      
    address = self.addr_strvar.get()
    password = self.pw_strvar.get()
    
    self.conn_submit_strvar.set("Attempting to connect...")
    
    self.connection = DirectConnection(address, password, self.log_request_error)
    
    self.connected = await self.connection.connect()
    if not self.connected:  
      return False
    
    req = simpleobsws.Request('GetVersion')
    ret = await self.connection.request(req)
    
    if not ret:
      self.connected = False
      return False

    self.platform = ret.responseData['platform']
    
    screenw, screenh = await self.get_video_settings()
    
    if not screenw or not screenh:
      return False
    else:
      self.output_width = screenw
      self.output_height = screenh
      return True
  
  async def get_video_settings(self):
    req = simpleobsws.Request('GetVideoSettings')
    ret = await self.connection.request(req)
    
    if not ret:
      self.connected = False
      return None, None
  
    return ret.responseData["baseWidth"], ret.responseData["baseHeight"]
  
  def find_scene_item(self, item_id : int) -> OBS_Object:
    for item in self.get_current_scene_items():
      if (item.scene_item_id == item_id):
        return item
    return None
  
  def find_uninit_item(self, sourceName : str) -> OBS_Object:
    for item in self.get_current_scene_items():
      if (item.source_name == sourceName) and \
         (item.scene_item_id == -1) and \
         (item.scene_item_index == -1):
           return item
    return None
  
  async def get_image_for_item(self, item : ImageInput) -> None:
    req = simpleobsws.Request('GetInputSettings', { 'inputName': item.source_name })
    ret = await self.connection.request(req)
    
    if ret and 'file' in ret.responseData['inputSettings']:
      url = ret.responseData['inputSettings']['file']
      item.set_url(url, False)
  
  async def get_text_settings(self, item : TextInput) -> None:
    req = simpleobsws.Request('GetInputSettings', { 'inputName': item.source_name })
    ret = await self.connection.request(req)
    
    if ret:
      settings = ret.responseData['inputSettings']
      if 'text' in settings:
        text = settings['text']
        item.set_text(text, False)
      if 'vertical' in settings:
        vertical = settings['vertical']
        item.set_vertical(vertical)
      if 'color' in settings:
        color = obs_to_color(settings['color'])
        item.set_color(color, False)
      if 'bk_color' in settings:
        bk_color = obs_to_color(settings['bk_color'])
        item.set_background_color(bk_color, False)
      if 'bk_opacity' in settings:
        bk_opacity = settings['bk_opacity']
        item.toggle_background((bk_opacity == 100), False)
  
  async def get_scene_state(self) -> None:
    req = simpleobsws.Request('GetCurrentProgramScene')
    ret = await self.connection.request(req)
    
    if not ret:
      logging.error("Failed to get current scene.")
      return False
    
    active_scene = ret.responseData["currentProgramSceneName"]
    if self.current_scene != active_scene:
      for item in self.get_current_scene_items():
        item.remove_from_canvas()
      self.current_scene = active_scene
      for item in self.get_current_scene_items():
        item.add_to_canvas()
      self.canvas_configure()
    
    screenw, screenh = await self.get_video_settings()
    if screenw and screenh:
      if self.output_height != screenh or self.output_width != screenw:
        self.output_width = screenw
        self.output_height = screenh
        self.screen.set_transform(w = self.output_width, h = self.output_height)
        self.canvas_configure()
    
    req = simpleobsws.Request('GetSceneItemList', { 'sceneName' : self.current_scene })
    ret = await self.connection.request(req)
    
    if not ret:
      logging.error("Failed to get scene items")
      return
    
    item_list = ret.responseData['sceneItems']
    
    for saved in self.get_current_scene_items()[:]:
      found = False
      if saved.scene_item_id == -1 and saved.scene_item_index == -1:
        found = True
        continue
      
      for active in item_list:
        if saved.scene_item_id == active['sceneItemId']:
          found = True
          break
      if not found:
        saved.remove_from_canvas()
        self.scenes[self.current_scene].remove(saved)
        
    for i in item_list:
      name = i['sourceName']
      itemId = i['sceneItemId']
      itemIndex = i['sceneItemIndex']
      kind = i['inputKind']
      
      item = self.find_scene_item(itemId)
      
      if not item:
        item = self.find_uninit_item(name)
      
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
      
      boundstype = tf['boundsType']
      
      if boundstype == 'OBS_BOUNDS_SCALE_INNER':
        w = tf['boundsWidth']
        h = tf['boundsHeight']
      
      if item:
        item.set_transform(x, y, w, h, (math.pi * a / 180.0), local = False)
        item.set_source_name(name, False)
        item.set_scene_item_id(itemId)
        item.scene_item_index = itemIndex
        item.source_width = sw
        item.source_height = sh
        item.bounds_type = boundstype
        
        if kind == 'image_source':
          await self.get_image_for_item(item)
        if kind == 'text_gdiplus_v2' or kind == 'text_ft2_source_v2':
          await self.get_text_settings(item)
        
      else:
        if kind == 'image_source':
          item = ImageInput(itemId, itemIndex, self.canvas, self.screen, x, y, w, h, a, sw, sh, boundstype, name)
          await self.get_image_for_item(item)
        elif kind == 'text_gdiplus_v2' or kind == 'text_ft2_source_v2':
          item = TextInput(itemId, itemIndex, self.canvas, self.screen, x, y, w, h, a, sw, sh, boundstype, name)
          await self.get_text_settings(item)
        else:
          item = OBS_Object(itemId, itemIndex, self.canvas, self.screen, x, y, w, h, a, sw, sh, boundstype, name)
          item.set_interactable(False)
          
        self.scenes[self.current_scene].append(item)
            
    # sort the scene items to match the OBS source list
    og_scenes = self.scenes[self.current_scene][:]
    self.scenes[self.current_scene] = sorted(self.scenes[self.current_scene], key = lambda item: item.scene_item_index if item.scene_item_index != -1 else 999, reverse = True)
    
    if og_scenes != self.scenes[self.current_scene]:
      for item in self.scenes[self.current_scene]:
        item.move_to_back()
      
  def queue_item_modification_requests(self) -> None:
    for item in self.get_current_scene_items():
      item.send_necessary_data(self)
    
  def log_request_error(self, resp : simpleobsws.RequestResponse) -> None:
    try:
      logging.error(f"Error {resp.requestStatus['code']}: {resp.requestStatus['comment']}")
    except:
      logging.error(resp)
      
  def save_scene_items(self) -> None:
    d : dict[str, list] = dict()
    for scene in self.scenes.keys():
      d[scene] = []
      for item in self.scenes[scene]:
        d[scene].append(item.to_dict())
        
    with open(self.savefile, 'w') as f:
      json.dump(d, f, indent = 2)
      
  def load_scene_items(self) -> None:
    if not (os.path.isfile(self.savefile) and os.path.exists(self.savefile)):
      return
    
    print("Loading scene items from save file.")
    
    with open(self.savefile, 'r') as f:
      d = json.load(f)
      
      item = None
      for scene in dict(d).keys():
        self.scenes[scene] = []
        for itemdict in d[scene]:
          if itemdict['type'] in list(user_types_map.keys()):
            item = user_types_map[itemdict['type']].from_dict(itemdict, self.canvas, self.screen)
          elif itemdict['type'] == "obs_object":
            item = OBS_Object.from_dict(itemdict, self.canvas, self.screen)
          else:
            logging.error("Unrecognized item type in save data. Skipping.")
            logging.error(f"Type: {itemdict['type']}")

          if item:
            item.remove_from_canvas()
            self.scenes[scene].append(item)
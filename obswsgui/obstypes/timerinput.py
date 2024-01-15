import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

import simpleobsws

from ..util.dtutil import TIME_FORMAT, strfdelta
from ..util.miscutil import hms_to_ms, ms_to_hms
from .obs_object import OBS_Object
from .countdowninput import CountdownInput
from .textinput import TextInput

class TimerInput(CountdownInput):
  total_time : float = 0 # in ms
  time_left_ms : float = 0 # in ms
  last_update : dt.datetime = None
  
  @staticmethod
  def description():
    return "Timer"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", hours : int = 0, minutes : int = 0, seconds : int = 0, time_left_ms = None, interactable : bool = True):
    TextInput.__init__(self, scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.total_time = hms_to_ms(hours, minutes, seconds)
    self.time_left_ms = time_left_ms if time_left_ms is not None else self.total_time
    
    self.hours_strvar = tk.StringVar(self.canvas, str(hours))
    self.minutes_strvar = tk.StringVar(self.canvas, str(minutes))
    self.seconds_strvar = tk.StringVar(self.canvas, str(seconds))
    
    self.last_update = dt.datetime.now()
  
  def calc_time(self):
    if self.time_left_ms == 0:
      return 
    
    time_passed = dt.datetime.now() - self.last_update
    
    self.time_left_ms -= 1000 * time_passed.total_seconds()
    self.time_left_ms = max(0, self.time_left_ms)
    
    self.set_text(strfdelta(dt.timedelta(milliseconds = self.time_left_ms), self.text_format))
    
    self.last_update = dt.datetime.now()
      
  def update_info(self) -> None:
    newhours   = int(self.hours_strvar.get())
    newminutes = int(self.minutes_strvar.get())
    newseconds = int(self.seconds_strvar.get())
    
    newtotal = hms_to_ms(newhours, newminutes, newseconds)
    
    diff = newtotal - self.total_time
    
    if diff != 0:
      self.total_time = newtotal
      self.time_left_ms += diff
      self.calc_time()
      
    OBS_Object.update_info(self)
  
  def setup_modify_duration(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    h, m, s, _ = ms_to_hms(self.total_time)
    
    self.modify_hours_label = ttk.Label(frame, text = "Hours:")
    self.modify_hours_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.hours_strvar.set(str(h))
    self.modify_hours_entry = ttk.Entry(frame, textvariable = self.hours_strvar)
    self.modify_hours_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.modify_minutes_label = ttk.Label(frame, text = "Minutes:")
    self.modify_minutes_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.minutes_strvar.set(str(m))
    self.modify_minutes_entry = ttk.Entry(frame, textvariable = self.minutes_strvar)
    self.modify_minutes_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.modify_seconds_label = ttk.Label(frame, text = "Seconds:")
    self.modify_seconds_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.seconds_strvar.set(str(s))
    self.modify_seconds_entry = ttk.Entry(frame, textvariable = self.seconds_strvar)
    self.modify_seconds_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_duration(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Color: ", lambda s: self.queue_set_input_color(gui, s), row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Background: ", lambda s: self.queue_set_input_background(gui, s), row)
    row = self.setup_background_toggle(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
  
  def to_dict(self) -> dict:
    d = OBS_Object.to_dict(self)
    d['type'] = self.description()
    d['total_time'] = self.total_time
    d['time_left_ms'] = self.time_left_ms
    d['color'] = self.color
    d['bk_color'] = self.bk_color
    d['bk_enabled'] = self.bk_enabled
    return d
    
  @staticmethod
  def setup_create_ui(gui : 'Default_GUI', frame : tk.Frame) -> None:
    row = 0
    row = OBS_Object.setup_add_input_name(gui, frame, row)
    
    gui.hours_label = ttk.Label(frame, text = "Hours", style = "Large.TLabel")
    gui.hours_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.string_param_1.set("0")
    gui.new_timer_hours_entry = ttk.Entry(frame, textvariable = gui.string_param_1, width = 48, **gui.largefontopt)
    gui.new_timer_hours_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    gui.minutes_label = ttk.Label(frame, text = "Minutes", style = "Large.TLabel")
    gui.minutes_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.string_param_2.set("0")
    gui.new_timer_minutes_entry = ttk.Entry(frame, textvariable = gui.string_param_2, width = 48, **gui.largefontopt)
    gui.new_timer_minutes_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    gui.seconds_label = ttk.Label(frame, text = "Seconds", style = "Large.TLabel")
    gui.seconds_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.string_param_3.set("0")
    gui.new_timer_seconds_entry = ttk.Entry(frame, textvariable = gui.string_param_3, width = 48, **gui.largefontopt)
    gui.new_timer_seconds_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    
    row = OBS_Object.setup_add_input_buttons(gui, frame, lambda: TimerInput.queue_add_input_request(gui), row)
  
  @staticmethod
  def queue_add_input_request(gui : 'Default_GUI') -> None:
    input_name = gui.new_input_name_strvar.get()
    input_hours    = int(gui.string_param_1.get())
    input_minutes  = int(gui.string_param_2.get())
    input_seconds  = int(gui.string_param_3.get())
    input_kind = 'text_gdiplus_v2' if gui.platform == "windows" else 'text_ft2_source_v2'
    
    inp = TimerInput(-1, -1, gui.canvas, gui.screen, 0, 0, 0, 0, 0, 0, 0, "", input_name, input_hours, input_minutes, input_seconds)
    gui.scenes[gui.current_scene].append(inp)
    
    if input_name != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': gui.current_scene, 'inputName': input_name, 'inputKind': input_kind, 'inputSettings': { 'text': "" }, 'sceneItemEnabled': True })
      gui.connection.queue_request(img_req)
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : OBS_Object) -> 'CountdownInput':
    h, m, s, _ = ms_to_hms(d['total_time'])
    cdin = TimerInput(d['scene_item_id'], d['scene_item_index'], canvas, screen, d['x'], d['y'], d['width'], d['height'], d['rotation'], d['source_width'], d['source_height'], d['bounds_type'], d['source_name'], h, m, s, d['time_left_ms'], d['interactable'])
    cdin.set_color(d['color'], False)
    cdin.set_background_color(d['bk_color'], False)
    cdin.toggle_background(d['bk_enabled'], False)
    return cdin
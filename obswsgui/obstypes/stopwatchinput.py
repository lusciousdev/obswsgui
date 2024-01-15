import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

import simpleobsws

from ..util.dtutil import strfdelta, TIME_FORMAT
from .obs_object import OBS_Object
from .textinput import TextInput

class StopwatchInput(TextInput):
  paused = False
  pause_time : dt.datetime = None
  start_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  
  @staticmethod
  def description():
    return "Stopwatch"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", start : dt.datetime = None, start_paused : bool = False, pause_time : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    start_time = start if start is not None else dt.datetime.now()
    
    self.start_time = start_time
    time_since = dt.datetime.now() - self.start_time
    if start_paused:
      self.paused = True
      self.pause_time = pause_time if pause_time is not None else start_time
      time_since = self.pause_time - self.start_time
    
    self.set_text(strfdelta(time_since, self.text_format))
  
  def update(self, gui : 'Default_GUI'):
    self.calc_time()
    
  def calc_time(self):
    if self.paused and self.pause_time:
      time_paused = (dt.datetime.now() - self.pause_time)
      self.start_time += time_paused
      self.pause_time = dt.datetime.now()
    else:
      time_since = dt.datetime.now() - self.start_time
      self.set_text(strfdelta(time_since, self.text_format))
      
  def update_info(self) -> None:
    OBS_Object.update_info(self)
    
  def toggle_pause(self, pause_button : ttk.Button = None):
    if self.paused:
      self.paused = False
      self.pause_time = None
      if pause_button:
        pause_button.configure(text = "Pause")
    else:
      self.paused = True
      self.pause_time = dt.datetime.now()
      if pause_button:
        pause_button.configure(text = "Unpause")
      
  def reset_timer(self):
    self.start_time = dt.datetime.now()
    self.set_text(strfdelta(dt.timedelta(seconds = 0), self.text_format))
    
  def setup_timer_buttons(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.pause_button = ttk.Button(frame, text = "Pause" if not self.paused else "Unpause", command = lambda: self.toggle_pause(self.pause_button))
    self.pause_button.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.reset_button = ttk.Button(frame, text = "Reset", command = self.reset_timer)
    self.reset_button.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_timer_buttons(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Color: ", lambda s: self.queue_set_input_color(gui, s), row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Background: ", lambda s: self.queue_set_input_background(gui, s), row)
    row = self.setup_background_toggle(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
  
  def to_dict(self) -> dict:
    d = OBS_Object.to_dict(self)
    d['type'] = self.description()
    d['start'] = self.start_time.strftime(TIME_FORMAT)
    d['paused'] = self.paused
    d['pause_time'] = None if (not self.paused) or (self.pause_time is None) else self.pause_time.strftime(TIME_FORMAT)
    d['color'] = self.color
    d['bk_color'] = self.bk_color
    d['bk_enabled'] = self.bk_enabled
    return d
  
  @staticmethod
  def setup_create_ui(gui : 'Default_GUI', frame : tk.Frame) -> None:
    row = 0
    row = OBS_Object.setup_add_input_name(gui, frame, row)
    
    gui.int_param_1.set(0)
    gui.timer_paused_entry = ttk.Checkbutton(frame, variable = gui.int_param_1, text = "Start paused?", style = "Large.TCheckbutton")
    gui.timer_paused_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    
    row = OBS_Object.setup_add_input_buttons(gui, frame, lambda: StopwatchInput.queue_add_input_request(gui), row)
  
  @staticmethod
  def queue_add_input_request(gui : 'Default_GUI') -> None:
    input_name = gui.new_input_name_strvar.get()
    input_kind = 'text_gdiplus_v2' if gui.platform == "windows" else 'text_ft2_source_v2'
    
    start_paused : bool = (gui.int_param_1.get() == 1)
    
    inp = StopwatchInput(-1, -1, gui.canvas, gui.screen, 0, 0, 0, 0, 0, 0, 0, "", input_name, None, start_paused, None)
    gui.scenes[gui.current_scene].append(inp)
    
    if input_name != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': gui.current_scene, 'inputName': input_name, 'inputKind': input_kind, 'inputSettings': { 'text': "" }, 'sceneItemEnabled': True })
      gui.connection.queue_request(img_req)
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : OBS_Object) -> 'StopwatchInput':
    id = d['scene_item_id']
    idx = d['scene_item_index']
    x = d['x']
    y = d['y']
    w = d['width']
    h = d['height']
    r = d['rotation']
    sw = d['source_width']
    sh = d['source_height']
    bt = d['bounds_type']
    name = d['source_name']
    start_time = dt.datetime.strptime(d['start'], TIME_FORMAT)
    paused = d['paused']
    pause_time = None if d['pause_time'] is None else dt.datetime.strptime(d['pause_time'], TIME_FORMAT)
    interactable = d['interactable']
    timerin = StopwatchInput(id, idx, canvas, screen, x, y, w, h, r, sw, sh, bt, name, start_time, paused, pause_time, interactable)
    timerin.set_color(d['color'], False)
    timerin.set_background_color(d['bk_color'], False)
    timerin.toggle_background(d['bk_enabled'], False)
    return timerin
  
import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

import simpleobsws

from ..util.dtutil import TIME_FORMAT, strfdelta
from .obs_object import OBS_Object
from .textinput import TextInput


class CountdownInput(TextInput):
  end_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  last_text : str = ""
  
  @staticmethod
  def description():
    return "Countdown"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", end : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.end_time = end
    self.hour_strvar = tk.StringVar(self.canvas, self.end_time.strftime(TIME_FORMAT))
  
  def update(self, gui : 'Default_GUI'):
    self.calc_time()
      
  def calc_time(self):
    time_til = self.end_time - dt.datetime.now()
    
    if time_til.total_seconds() > 0:
      self.set_text(strfdelta(time_til, self.text_format))
    else:
      time_til = dt.timedelta(seconds = 0)
      self.set_text(strfdelta(time_til, self.text_format))
      
  def update_info(self) -> None:
    newend = self.hour_strvar.get()
    newdt = dt.datetime.strptime(newend, TIME_FORMAT)
    
    if self.end_time != newdt:
      self.end_time = newdt
      self.calc_time()
      
    OBS_Object.update_info(self)
  
  def setup_modify_end(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_end_label = ttk.Label(frame, text = "End time (YYYY-mm-dd HH:MM:SS):")
    self.modify_end_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.hour_strvar.set(self.end_time.strftime(TIME_FORMAT))
    self.modify_end_entry = ttk.Entry(frame, textvariable = self.hour_strvar)
    self.modify_end_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_end(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Color: ", lambda s: self.queue_set_input_color(gui, s), row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Background: ", lambda s: self.queue_set_input_background(gui, s), row)
    row = self.setup_background_toggle(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
  
  def to_dict(self) -> dict:
    d = OBS_Object.to_dict(self)
    d['type'] = self.description()
    d['end'] = self.end_time.strftime(TIME_FORMAT)
    d['color'] = self.color
    d['bk_color'] = self.bk_color
    d['bk_enabled'] = self.bk_enabled
    return d
    
  @staticmethod
  def setup_create_ui(gui : 'Default_GUI', frame : tk.Frame) -> None:
    row = 0
    row = OBS_Object.setup_add_input_name(gui, frame, row)
    
    gui.timer_info_label = ttk.Label(frame, text = "End time (YYYY-mm-dd HH:MM:SS)", style = "Large.TLabel")
    gui.timer_info_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.string_param_1.set((dt.datetime.now() + dt.timedelta(hours = 1)).strftime(TIME_FORMAT))
    gui.new_countdown_end_entry = ttk.Entry(frame, textvariable = gui.string_param_1, width = 48, **gui.largefontopt)
    gui.new_countdown_end_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    
    row = OBS_Object.setup_add_input_buttons(gui, frame, lambda: CountdownInput.queue_add_input_request(gui), row)
  
  @staticmethod
  def queue_add_input_request(gui : 'Default_GUI') -> None:
    input_name = gui.new_input_name_strvar.get()
    input_end  = gui.string_param_1.get()
    input_kind = 'text_gdiplus_v2' if gui.platform == "windows" else 'text_ft2_source_v2'
    
    enddt = dt.datetime.strptime(input_end, TIME_FORMAT)
    
    inp = CountdownInput(-1, -1, gui.canvas, gui.screen, 0, 0, 0, 0, 0, 0, 0, "", input_name, enddt)
    gui.scenes[gui.current_scene].append(inp)
    
    if input_name != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': gui.current_scene, 'inputName': input_name, 'inputKind': input_kind, 'inputSettings': { 'text': "" }, 'sceneItemEnabled': True })
      gui.connection.queue_request(img_req)
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : OBS_Object) -> 'CountdownInput':
    cdin = CountdownInput(d['scene_item_id'], d['scene_item_index'], canvas, screen, d['x'], d['y'], d['width'], d['height'], d['rotation'], d['source_width'], d['source_height'], d['bounds_type'], d['source_name'], dt.datetime.strptime(d['end'], TIME_FORMAT), d['interactable'])
    cdin.set_color(d['color'], False)
    cdin.set_background_color(d['bk_color'], False)
    cdin.toggle_background(d['bk_enabled'], False)
    return cdin
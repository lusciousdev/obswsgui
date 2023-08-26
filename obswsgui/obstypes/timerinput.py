import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

from ..util.dtutil import strfdelta
from .obs_object import OBS_Object
from .textinput import TextInput

class TimerInput(TextInput):
  paused = False
  pause_time : dt.datetime = None
  start_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", start : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.start_time = start
  
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
    
  def setup_timer_buttons(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.pause_button = ttk.Button(frame, text = "Pause", command = lambda: self.toggle_pause(self.pause_button))
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
  
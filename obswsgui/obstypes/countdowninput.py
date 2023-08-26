import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

from ..util.dtutil import COUNTDOWN_END_FORMAT, strfdelta
from .obs_object import OBS_Object
from .textinput import TextInput


class CountdownInput(TextInput):
  end_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  last_text : str = ""
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", end : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.end_time = end
    self.end_strvar = tk.StringVar(self.canvas, self.end_time.strftime(COUNTDOWN_END_FORMAT))
  
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
    newend = self.end_strvar.get()
    newdt = dt.datetime.strptime(newend, COUNTDOWN_END_FORMAT)
    
    if self.end_time != newdt:
      self.end_time = newdt
      self.calc_time()
      
    OBS_Object.update_info(self)
  
  def setup_modify_end(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_end_label = ttk.Label(frame, text = "Text:")
    self.modify_end_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_end_entry = ttk.Entry(frame, textvariable = self.end_strvar)
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
import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

from ..util.dtutil import strfdelta
from .obs_object import OBS_Object
from .textinput import TextInput

class CounterInput(TextInput):
  counter = 0
  counter_standin = "__count__"
  counter_format = "__count__"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", counter_format : str = "{}", interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.counter_format = counter_format
    
    self.format_strvar = tk.StringVar(self.canvas, self.counter_format)
    
  def get_formatted_counter(self) -> str:
    try:
      newtext = self.counter_format.replace(self.counter_standin, str(self.counter))
    except:
      newtext = self.counter_format
      
    return newtext
  
  def update_info(self) -> None:
    self.counter_format = self.format_strvar.get()
      
    self.set_text(self.get_formatted_counter())
      
    OBS_Object.update_info(self)
  
  def setup_modify_format(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_format_label = ttk.Label(frame, text = f"Format: ({self.counter_standin} is replaced)")
    self.modify_format_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_format_entry = ttk.Entry(frame, textvariable = self.format_strvar)
    self.modify_format_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_counter_buttons(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.counterframe = ttk.Frame(frame, padding = "0 0 0 10")
    self.counterframe.grid(column = 0, row = row, sticky = (tk.W, tk.E))
    self.counterframe.columnconfigure(0, weight = 1, uniform = "counterbuttons")
    self.counterframe.columnconfigure(1, weight = 1, uniform = "counterbuttons")
    row += 1
    
    def dec():
      self.counter -= 1
      self.update_info()
    self.decrement = ttk.Button(self.counterframe, text = "--", command = dec)
    self.decrement.grid(column = 0, row = 0, padx = (2, 2), sticky = (tk.W, tk.E))
    def inc():
      self.counter += 1
      self.update_info()
    self.increment = ttk.Button(self.counterframe, text = "++", command = inc)
    self.increment.grid(column = 1, row = 0, padx = (2, 2), sticky = (tk.W, tk.E))
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_format(gui, gui.modifyframe, row)
    row = self.setup_counter_buttons(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Color: ", lambda s: self.queue_set_input_color(gui, s), row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Background: ", lambda s: self.queue_set_input_background(gui, s), row)
    row = self.setup_background_toggle(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
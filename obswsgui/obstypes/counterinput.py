import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI
  
import simpleobsws

from ..util.dtutil import strfdelta
from .obs_object import OBS_Object
from .textinput import TextInput

class CounterInput(TextInput):
  counter = 0
  counter_standin = "__count__"
  counter_format = "__count__"
  
  @staticmethod
  def description():
    return "Counter"
  
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
  
  def to_dict(self) -> dict:
    d = OBS_Object.to_dict(self)
    d['type'] = self.description()
    d['format'] = self.counter_format
    d['count'] = self.counter
    d['color'] = self.color
    d['bk_color'] = self.bk_color
    d['bk_enabled'] = self.bk_enabled
    return d
  
  @staticmethod
  def setup_create_ui(gui : 'Default_GUI', frame : tk.Frame) -> None:
    row = 0
    row = OBS_Object.setup_add_input_name(gui, frame, row)
    
    gui.counter_info_label = ttk.Label(frame, text = "Counter format (__count__ gets replaced):", style = "Large.TLabel")
    gui.counter_info_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.string_param_1.set("Current count is __count__.")
    gui.new_counter_entry = ttk.Entry(frame, textvariable = gui.string_param_1, width = 48, **gui.largefontopt)
    gui.new_counter_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    
    row = OBS_Object.setup_add_input_buttons(gui, frame, lambda: CounterInput.queue_add_input_request(gui), row)
  
  @staticmethod
  def queue_add_input_request(gui : 'Default_GUI') -> None:
    input_name = gui.new_input_name_strvar.get()
    counter_format = gui.string_param_1.get()
    input_kind = 'text_gdiplus_v2' if gui.platform == "windows" else 'text_ft2_source_v2'
    
    inp = CounterInput(-1, -1, gui.canvas, gui.screen, 0, 0, 0, 0, 0, 0, 0, "", input_name, counter_format)
    gui.scenes[gui.current_scene].append(inp)
    
    if input_name != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': gui.current_scene, 'inputName': input_name, 'inputKind': input_kind, 'inputSettings': { 'text': inp.get_formatted_counter() }, 'sceneItemEnabled': True })
      gui.connection.queue_request(img_req)
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : OBS_Object) -> 'CounterInput':
    counterin = CounterInput(d['scene_item_id'], d['scene_item_index'], canvas, screen, d['x'], d['y'], d['width'], d['height'], d['rotation'], d['source_width'], d['source_height'], d['bounds_type'], d['source_name'], d['format'], d['interactable'])
    counterin.counter = d['count']
    counterin.set_color(d['color'], False)
    counterin.set_background_color(d['bk_color'], False)
    counterin.toggle_background(d['bk_enabled'], False)
    return counterin
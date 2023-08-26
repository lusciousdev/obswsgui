import datetime as dt
import math
import tkinter as tk
from string import Template
from tkinter import font, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

import simpleobsws

from ..util.miscutil import color_to_obs
from ..util.dtutil import strfdelta
from .obs_object import OBS_Object

class TextInput(OBS_Object):
  text = ""
  text_changed = False
  text_id = None
  
  text_font = None
  
  vertical = False
  
  color = "#ffffff"
  bk_color = "#000000"
  bk_enabled = False
  color_changed = False
  
  text_strvar = None
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.text_font = font.Font(family="Helvetica", size = 1)
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.text_id = self.canvas.create_text((self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0, fill = self.color, text = self.text, font = self.text_font, anchor = tk.CENTER)
    
    self.text_strvar = tk.StringVar(self.canvas)
    
  def send_necessary_data(self, gui : 'Default_GUI') -> None:
    if self.text_changed:
      self.queue_set_input_text(gui)
      self.text_changed = False
    if self.color_changed:
      self.queue_set_input_color(gui)
      self.queue_set_input_background(gui)
      self.color_changed = False
      
    return super().send_necessary_data(gui)
    
  def remove_from_canvas(self) -> None:
    if self.text_id:
      self.canvas.delete(self.text_id)
      self.text_id = None
    return super().remove_from_canvas()
  
  def add_to_canvas(self) -> None:
    super().add_to_canvas()
    if self.text_id is None:
      self.text_id = self.canvas.create_text((self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0, fill = self.color, text = self.text, font = self.text_font, anchor = tk.CENTER)
  
  def get_font_size(self) -> None:
    text_height = self.text_font.metrics('linespace')
    text_width = self.text_font.measure(self.text)
    font_size = self.text_font.actual('size')
    
    if abs(self.hpx) < 1 or abs(self.wpx) < 1:
      self.text_font.config(size = 1)
      return
    
    while text_height < abs(self.hpx) and text_width < abs(self.wpx):
      font_size += 1
      self.text_font.config(size = font_size)
      
      text_height = self.text_font.metrics('linespace')
      text_width = self.text_font.measure(self.text)
      
    while (text_height > abs(self.hpx) or text_width > abs(self.wpx)) and font_size > 0:
      font_size -= 1
      self.text_font.config(size = font_size)
      
      text_height = self.text_font.metrics('linespace')
      text_width = self.text_font.measure(self.text)
    
  def set_text(self, text : str, local : bool = True) -> None:
    if self.text_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return
    
    if self.text != text:
      self.text = text
      self.text_strvar.set(self.text)
        
      self.canvas.itemconfigure(self.text_id, text = self.text)
      
      self.text_changed |= local
      
  def set_color(self, color : str, local = True) -> None:
    if self.color_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return 
    
    if self.color != color:
      self.color = color
      self.canvas.itemconfigure(self.text_id, fill = self.color)
      
      self.color_changed |= local
      
  def set_background_color(self, bk_color : str, local = True) -> None:
    if self.color_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return 
    
    if self.bk_color != bk_color:
      self.bk_color = bk_color
      
      if self.bk_enabled:
        self.canvas.itemconfigure(self.rect_id, fill = self.bk_color)
      else:
        self.canvas.itemconfigure(self.rect_id, fill = "")
      
      self.color_changed |= local
      
  def toggle_background(self, bk_enable : str, local = True) -> None:
    if self.color_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return 
    
    if self.bk_enabled != bk_enable:
      self.bk_enabled = bk_enable
      
      if self.bk_enabled:
        self.canvas.itemconfigure(self.rect_id, fill = self.bk_color)
      else:
        self.canvas.itemconfigure(self.rect_id, fill = "")
      
      self.color_changed |= local
      
  def set_vertical(self, vertical : bool) -> None:
    if self.vertical != vertical:
      self.vertical = vertical
      self.canvas.itemconfigure(self.text_id, angle = 0 if not self.vertical else 270, anchor = tk.CENTER)
      
  def move_to_front(self, under : int = None) -> None:
    last_id = self.move_id_to_front(self.text_id, under)
    return super().move_to_front(last_id)
  
  def move_to_back(self, above : int = None) -> None:
    last_id = self.move_id_to_back(self.text_id, above)
    return super().move_to_back(last_id)
      
  def redraw(self) -> None:
    super().redraw()
    
    self.get_font_size()
    
    if self.text_id:
      self.canvas.coords(self.text_id, (self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0)
      self.canvas.itemconfig(self.text_id, font = self.text_font, angle = (-180.0 * self.rotation / math.pi))
      
  def queue_set_input_text(self, gui : 'Default_GUI'):
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'text': self.text }})
    gui.connection.queue_request(req)
    
  def queue_set_input_color(self, gui : 'Default_GUI', color : str = None):
    c = self.color if not color else color
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'color': color_to_obs(c) }})
    gui.connection.queue_request(req)
    
  def queue_set_input_background(self, gui : 'Default_GUI', color : str = None):
    c = self.bk_color if not color else color
    o = 100 if self.bk_enabled else 0
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'bk_color': color_to_obs(c), 'bk_opacity': o }})
    gui.connection.queue_request(req)
      
  def update_info(self) -> None:
    newtext = self.text_strvar.get()
    
    if self.text != newtext:
      self.set_text(newtext)
    
    return super().update_info()
  
  def setup_modify_text(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_text_label = ttk.Label(frame, text = "Text:")
    self.modify_text_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_text_entry = ttk.Entry(frame, textvariable = self.text_strvar, validate = 'all', validatecommand=(gui.modifyframe.register(lambda val: self.adjust_modify_ui(gui, val)), '%P'))
    self.modify_text_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_background_toggle(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.background_toggle_frame = ttk.Frame(frame, padding = "0 0 0 10")
    self.background_toggle_frame.grid(column = 0, row = row, sticky = (tk.W, tk.E))
    self.background_toggle_frame.columnconfigure(1, weight = 1)
    row += 1
    
    self.background_toggle_label = ttk.Label(self.background_toggle_frame, text = "Background? ")
    self.background_toggle_label.grid(column = 0, row = 0, sticky = tk.W)
    
    self.background_toggle_boolvar = tk.BooleanVar(frame, self.bk_enabled)
    self.background_toggle_checkbox = tk.Checkbutton(self.background_toggle_frame, offvalue = False, onvalue = True, variable = self.background_toggle_boolvar, command = lambda: self.toggle_background(self.background_toggle_boolvar.get()), bg = gui.background_color, activebackground = gui.background_button)
    self.background_toggle_checkbox.grid(column = 1, row = 0, sticky = tk.W)
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    super().setup_modify_ui(gui)
    row = 0
    
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_text(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Color: ", lambda s: self.set_color(s), row)
    row = self.setup_color_picker(gui, gui.modifyframe, "Background: ", lambda s: self.set_background_color(s), row)
    row = self.setup_background_toggle(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
    
    return super().setup_modify_ui(gui)
  
  def to_dict(self) -> dict:
    d = super().to_dict()
    d['type'] = "textinput"
    d['text'] = self.text
    d['color'] = self.color
    d['bk_color'] = self.bk_color
    d['bk_enabled'] = self.bk_enabled
    return d
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : OBS_Object) -> 'TextInput':
    textin = TextInput(d['scene_item_id'], d['scene_item_index'], canvas, screen, d['x'], d['y'], d['width'], d['height'], d['rotation'], d['source_width'], d['source_height'], d['bounds_type'], d['source_name'], d['interactable'])
    textin.set_text(d['text'], False)
    textin.set_color(d['color'], False)
    textin.set_background_color(d['bk_color'], False)
    textin.toggle_background(d['bk_enabled'], False)
    return textin
import datetime as dt
import math
import tkinter as tk
from string import Template
from tkinter import font, ttk

import simpleobsws

import miscutil
import obs_object as obsobj

COUNTDOWN_END_FORMAT = "%Y-%m-%d %H:%M:%S"

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)

class TextInput(obsobj.OBS_Object):
  text = ""
  text_id = None
  
  text_font = None
  
  vertical = False
  color = "#fff"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.text_font = font.Font(family="Helvetica", size = 1)
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.text_id = self.canvas.create_text((self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0, fill = self.default_color, text = self.text, font = self.text_font, anchor = tk.CENTER)
    
  def remove_from_canvas(self) -> None:
    if self.text_id:
      self.canvas.delete(self.text_id)
    return super().remove_from_canvas()
  
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
    
  def set_text(self, text : str) -> None:
    if self.text != text:
      self.text = text
      self.canvas.itemconfigure(self.text_id, text = self.text)
      
  def set_color(self, color : str) -> None:
    if self.color != color:
      self.color = color
      self.canvas.itemconfigure(self.text_id, fill = self.color)
      
  def set_vertical(self, vertical : bool) -> None:
    if self.vertical != vertical:
      self.vertical = vertical
      self.canvas.itemconfigure(self.text_id, angle = 0 if not self.vertical else 270, anchor = tk.CENTER)
      
  def move_to_front(self, under : obsobj.OBS_Object = None) -> None:
    if self.text_id:
      if under:
        self.canvas.tag_raise(self.text_id, under)
      else:
        self.canvas.tag_raise(self.text_id)
        
    return super().move_to_front(self.text_id)
      
  def redraw(self) -> None:
    super().redraw()
    
    self.get_font_size()
    
    if self.text_id:
      self.canvas.coords(self.text_id, (self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0)
      self.canvas.itemconfig(self.text_id, font = self.text_font, angle = (-180.0 * self.rotation / math.pi))
      
  def update_input_text(self, gui : 'owg.OBS_WS_GUI'):
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'text': self.text }})
    gui.requests_queue.append(req)
    
  def update_text_color(self, gui : 'owg.OBS_WS_GUI', color : str = None):
    c = self.color if not color else color
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'color': miscutil.color_to_obs(c) }})
    gui.requests_queue.append(req)
      
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    newtext = self.modify_text_strvar.get()
    
    if self.text != newtext:
      self.set_text(newtext)
      self.update_input_text(gui)
    
    return super().queue_update_req(gui)
  
  def adjust_modify_ui(self, gui : 'owg.OBS_WS_GUI', val : str) -> None:
    if (val.isnumeric()):
      self.counterframe.grid()
    else:
      self.counterframe.grid_remove()
    return True
  
  def setup_color_picker(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame) -> None:
    def set_color(color: str):
      self.update_text_color(gui, color)
    
    self.set_white  = tk.Button(frame, command = lambda: set_color("#ffffff"), bg = "#ffffff")
    self.set_white.grid(column = 0, row = 0, sticky = (tk.W, tk.E))
    self.set_black  = tk.Button(frame, command = lambda: set_color("#000000"), bg = "#000000")
    self.set_black.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    self.set_red    = tk.Button(frame, command = lambda: set_color("#ff0000"), bg = "#ff0000")
    self.set_red.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    self.set_green  = tk.Button(frame, command = lambda: set_color("#00ff00"), bg = "#00ff00")
    self.set_green.grid(column = 1, row = 1, sticky = (tk.W, tk.E))
    self.set_blue   = tk.Button(frame, command = lambda: set_color("#0000ff"), bg = "#0000ff")
    self.set_blue.grid(column = 2, row = 0, sticky = (tk.W, tk.E))
    self.set_purple = tk.Button(frame, command = lambda: set_color("#ff00ff"), bg = "#ff00ff")
    self.set_purple.grid(column = 2, row = 1, sticky = (tk.W, tk.E))
    self.set_yellow = tk.Button(frame, command = lambda: set_color("#ffff00"), bg = "#ffff00")
    self.set_yellow.grid(column = 3, row = 0, sticky = (tk.W, tk.E))
    self.set_cyan   = tk.Button(frame, command = lambda: set_color("#00ffff"), bg = "#00ffff")
    self.set_cyan.grid(column = 3, row = 1, sticky = (tk.W, tk.E))
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    gui.modifyframe.columnconfigure(0, weight = 1)
    
    self.modify_name_label = ttk.Label(gui.modifyframe, text = "Name:")
    self.modify_name_label.grid(column = 0, row = 0, sticky = tk.W)
    
    self.modify_name_strvar = tk.StringVar(gui.root, self.source_name)
    self.modify_name_entry = ttk.Entry(gui.modifyframe, textvariable=self.modify_name_strvar)
    self.modify_name_entry.grid(column = 0, row = 1, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.modify_text_label = ttk.Label(gui.modifyframe, text = "Text:")
    self.modify_text_label.grid(column = 0, row = 2, sticky = tk.W)
    
    self.modify_text_strvar = tk.StringVar(gui.root, self.text)
    
    self.modify_text_entry = ttk.Entry(gui.modifyframe, textvariable = self.modify_text_strvar, validate = 'all', validatecommand=(gui.modifyframe.register(lambda val: self.adjust_modify_ui(gui, val)), '%P'))
    self.modify_text_entry.grid(column = 0, row = 3, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.counterframe = ttk.Frame(gui.modifyframe, padding = "0 0 0 10")
    self.counterframe.grid(column = 0, row = 4, sticky = (tk.W, tk.E))
    self.counterframe.columnconfigure(0, weight = 1, uniform = "counterbuttons")
    self.counterframe.columnconfigure(1, weight = 1, uniform = "counterbuttons")
    def dec():
      val = int(self.modify_text_strvar.get()) - 1
      self.modify_text_strvar.set(f"{val}")
      self.queue_update_req(gui)
    self.decrement = ttk.Button(self.counterframe, text = "--", command = dec, width = 10)
    self.decrement.grid(column = 0, row = 0, padx = (2, 2), sticky = (tk.W, tk.E))
    def inc():
      val = int(self.modify_text_strvar.get()) + 1
      self.modify_text_strvar.set(f"{val}")
      self.queue_update_req(gui)
    self.increment = ttk.Button(self.counterframe, text = "++", command = inc)
    self.increment.grid(column = 1, row = 0, padx = (2, 2), sticky = (tk.W, tk.E))
    
    self.update_button = ttk.Button(gui.modifyframe, text = "Update", command = lambda: self.setup_update_dialog(gui))
    self.update_button.grid(column = 0, row = 5, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.modify_color_label = ttk.Label(gui.modifyframe, text = "Color:")
    self.modify_color_label.grid(column = 0, row = 6, sticky = tk.W)
    
    self.modify_color_frame = ttk.Frame(gui.modifyframe, padding = "2 0 2 10")
    self.modify_color_frame.grid(column = 0, row = 7, rowspan = 2, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.modify_color_frame.columnconfigure(0, weight = 1)
    self.modify_color_frame.columnconfigure(1, weight = 1)
    self.modify_color_frame.columnconfigure(2, weight = 1)
    self.modify_color_frame.columnconfigure(3, weight = 1)
    
    self.setup_color_picker(gui, self.modify_color_frame)
    
    self.dupimage = ttk.Button(gui.modifyframe, text = "Duplicate", command = lambda: self.setup_duplicate_dialog(gui))
    self.dupimage.grid(column = 0, row = 9, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Delete", command = lambda: self.setup_delete_dialog(gui))
    self.deleteimage.grid(column = 0, row = 10, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = 11, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.adjust_modify_ui(gui, self.modify_text_strvar.get())
    
    return super().setup_modify_ui(gui)
  
class CountdownInput(TextInput):
  end_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  last_text : str = ""
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", end : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.end_time = end
  
  def update(self, gui : 'owg.OBS_WS_GUI'):
    time_til = self.end_time - dt.datetime.now()
    self.set_text(strfdelta(time_til, self.text_format))
    
    if self.last_text != self.text:
      self.update_input_text(gui)
      self.last_text = self.text
      
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    newend = self.modify_end_strvar.get()
    newdt = dt.datetime.strptime(newend, COUNTDOWN_END_FORMAT)
    
    if self.end_time != newdt:
      self.end_time = newdt
      self.update(gui)
      
    obsobj.OBS_Object.queue_update_req(self, gui)
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    gui.modifyframe.columnconfigure(0, weight = 1)
    
    self.modify_name_label = ttk.Label(gui.modifyframe, text = "Name:")
    self.modify_name_label.grid(column = 0, row = 0, sticky = tk.W)
    
    self.modify_name_strvar = tk.StringVar(gui.root, self.source_name)
    self.modify_name_entry = ttk.Entry(gui.modifyframe, textvariable=self.modify_name_strvar)
    self.modify_name_entry.grid(column = 0, row = 1, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.modify_end_label = ttk.Label(gui.modifyframe, text = "End time:")
    self.modify_end_label.grid(column = 0, row = 2, sticky = tk.W)
    
    self.modify_end_strvar = tk.StringVar(gui.root, self.end_time.strftime(COUNTDOWN_END_FORMAT))
    self.modify_end_entry = ttk.Entry(gui.modifyframe, textvariable = self.modify_end_strvar)
    self.modify_end_entry.grid(column = 0, row = 3, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.update_button = ttk.Button(gui.modifyframe, text = "Update", command = lambda: self.setup_update_dialog(gui))
    self.update_button.grid(column = 0, row = 5, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.modify_color_label = ttk.Label(gui.modifyframe, text = "Color:")
    self.modify_color_label.grid(column = 0, row = 6, sticky = tk.W)
    
    self.modify_color_frame = ttk.Frame(gui.modifyframe, padding = "2 0 2 10")
    self.modify_color_frame.grid(column = 0, row = 7, rowspan = 2, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.modify_color_frame.columnconfigure(0, weight = 1)
    self.modify_color_frame.columnconfigure(1, weight = 1)
    self.modify_color_frame.columnconfigure(2, weight = 1)
    self.modify_color_frame.columnconfigure(3, weight = 1)
    
    self.setup_color_picker(gui, self.modify_color_frame)
    
    self.dupimage = ttk.Button(gui.modifyframe, text = "Duplicate", command = lambda: self.setup_duplicate_dialog(gui))
    self.dupimage.grid(column = 0, row = 9, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Delete", command = lambda: self.setup_delete_dialog(gui))
    self.deleteimage.grid(column = 0, row = 10, sticky = (tk.W, tk.E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = 11, sticky = (tk.W, tk.E), pady = (0, 5))

import obswsgui as owg

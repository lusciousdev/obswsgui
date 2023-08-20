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
  
  text_changed = False
  
  modify_text_strvar = None
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.text_font = font.Font(family="Helvetica", size = 1)
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.text_id = self.canvas.create_text((self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0, fill = self.color, text = self.text, font = self.text_font, anchor = tk.CENTER)
    
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
      if self.modify_text_strvar:
        self.modify_text_strvar.set(self.text)
        
      self.canvas.itemconfigure(self.text_id, text = self.text)
      
      self.text_changed |= local
      
  def set_color(self, color : str) -> None:
    if self.color != color:
      self.color = color
      self.canvas.itemconfigure(self.text_id, fill = self.color)
      
  def set_vertical(self, vertical : bool) -> None:
    if self.vertical != vertical:
      self.vertical = vertical
      self.canvas.itemconfigure(self.text_id, angle = 0 if not self.vertical else 270, anchor = tk.CENTER)
      
  def move_to_front(self, under : int = None) -> None:
    if self.text_id:
      if under:
        self.canvas.tag_raise(self.text_id, under)
      else:
        self.canvas.tag_raise(self.text_id)
        
    return super().move_to_front(self.text_id)
  
  def move_to_back(self, above : int = None) -> None:
    if self.text_id:
      if above:
        self.canvas.tag_lower(self.text_id, above)
      else:
        self.canvas.tag_lower(self.text_id)
        
    return super().move_to_back(self.text_id)
      
  def redraw(self) -> None:
    super().redraw()
    
    self.get_font_size()
    
    if self.text_id:
      self.canvas.coords(self.text_id, (self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0)
      self.canvas.itemconfig(self.text_id, font = self.text_font, angle = (-180.0 * self.rotation / math.pi))
      
  def update_input_text(self, gui : 'owg.OBS_WS_GUI'):
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'text': self.text }})
    gui.connection.queue_request(req)
    
  def update_text_color(self, gui : 'owg.OBS_WS_GUI', color : str = None):
    c = self.color if not color else color
    req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'color': miscutil.color_to_obs(c) }})
    gui.connection.queue_request(req)
      
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    newtext = self.modify_text_strvar.get()
    
    if self.text != newtext:
      self.set_text(newtext)
    
    return super().queue_update_req(gui)
  
  def adjust_modify_ui(self, gui : 'owg.OBS_WS_GUI', val : str) -> None:
    if (val.isnumeric()):
      self.counterframe.grid()
    else:
      self.counterframe.grid_remove()
    return True
  
  def setup_modify_text(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_text_label = ttk.Label(frame, text = "Text:")
    self.modify_text_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_text_strvar = tk.StringVar(gui.root, self.text)
    self.modify_text_entry = ttk.Entry(frame, textvariable = self.modify_text_strvar, validate = 'all', validatecommand=(gui.modifyframe.register(lambda val: self.adjust_modify_ui(gui, val)), '%P'))
    self.modify_text_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_counter_buttons(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.counterframe = ttk.Frame(frame, padding = "0 0 0 10")
    self.counterframe.grid(column = 0, row = row, sticky = (tk.W, tk.E))
    self.counterframe.columnconfigure(0, weight = 1, uniform = "counterbuttons")
    self.counterframe.columnconfigure(1, weight = 1, uniform = "counterbuttons")
    row += 1
    
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
    
    return row
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    super().setup_modify_ui(gui)
    row = 0
    
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_text(gui, gui.modifyframe, row)
    row = self.setup_counter_buttons(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, lambda s: self.update_text_color(gui, s), row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
    
    self.adjust_modify_ui(gui, self.modify_text_strvar.get())
    
    return super().setup_modify_ui(gui)
  
class TimerInput(TextInput):
  paused = False
  pause_time : dt.datetime = None
  start_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  last_text : str = ""
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", start : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.start_time = start
  
  def update(self, gui : 'owg.OBS_WS_GUI'):
    if self.paused and self.pause_time:
      time_paused = (dt.datetime.now() - self.pause_time)
      self.start_time += time_paused
      self.pause_time = dt.datetime.now()
    else:
      time_since = dt.datetime.now() - self.start_time
      self.set_text(strfdelta(time_since, self.text_format))
      
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    obsobj.OBS_Object.queue_update_req(self, gui)
    
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
    
  def setup_timer_buttons(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.pause_button = ttk.Button(frame, text = "Pause", command = lambda: self.toggle_pause(self.pause_button))
    self.pause_button.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.reset_button = ttk.Button(frame, text = "Reset", command = self.reset_timer)
    self.reset_button.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    obsobj.OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_timer_buttons(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, lambda s: self.update_text_color(gui, s), row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
  
class CountdownInput(TextInput):
  end_time : dt.datetime = None
  text_format : str = '%H:%M:%S'
  last_text : str = ""
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", end : dt.datetime = None, interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.end_time = end
  
  def update(self, gui : 'owg.OBS_WS_GUI'):
    time_til = self.end_time - dt.datetime.now()
    
    if time_til.total_seconds() > 0:
      self.set_text(strfdelta(time_til, self.text_format))
    else:
      time_til = dt.timedelta(seconds = 0)
      self.set_text(strfdelta(time_til, self.text_format))
      
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    newend = self.modify_end_strvar.get()
    newdt = dt.datetime.strptime(newend, COUNTDOWN_END_FORMAT)
    
    if self.end_time != newdt:
      self.end_time = newdt
      self.update(gui)
      
    obsobj.OBS_Object.queue_update_req(self, gui)
  
  def setup_modify_end(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_end_label = ttk.Label(frame, text = "Text:")
    self.modify_end_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_end_strvar = tk.StringVar(gui.root, self.end_time.strftime(COUNTDOWN_END_FORMAT))
    self.modify_end_entry = ttk.Entry(frame, textvariable = self.modify_end_strvar)
    self.modify_end_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    obsobj.OBS_Object.setup_modify_ui(self, gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_end(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_color_picker(gui, gui.modifyframe, lambda s: self.update_text_color(gui, s), row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)

import obswsgui as owg

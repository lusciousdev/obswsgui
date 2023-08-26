import math
import tkinter as tk
from tkinter import ttk

import requests
import simpleobsws
from PIL import Image, ImageTk

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

from .obs_object import OBS_Object

class ImageInput(OBS_Object):
  img_url = ""
  url_changed = False
  img_id = None
  orig_img = None
  resized_img = None
  transformed_img = None
  tk_img = None
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, rotation, source_width, source_height, bounds_type, label, interactable)
    self.url_strvar = tk.StringVar(self.canvas, self.img_url)
    
  def send_necessary_data(self, gui: 'Default_GUI') -> None:
    if self.url_changed:
      self.queue_set_input_url(gui)
    
    return super().send_necessary_data(gui)
 
  def remove_from_canvas(self) -> None:
    super().remove_from_canvas()
    if self.img_id:
      self.canvas.delete(self.img_id)
      self.img_id = None
      
  def add_to_canvas(self) -> None:
    super().add_to_canvas()
    if self.img_id is None:
      self.img_id = self.canvas.create_image(0, 0, image = self.tk_img, anchor = tk.NW)
  
  def redraw(self) -> None:
    super().redraw()
    
    if self.orig_img:
      imgx = self.polygon.minx()
      imgy = self.polygon.miny()
      imgw = int(self.wpx)
      imgh = int(self.hpx)
      flip_hori = False
      flip_vert = False
      
      if imgw == 0:
        imgw = 1
      if imgw < 0:
        imgw = abs(imgw) 
        flip_hori = True
        
      if imgh == 0:
        imgh = 1
      if imgh < 0:
        imgh = abs(imgh)
        flip_vert = True 
        
      self.resized_img = self.orig_img.resize((imgw, imgh))
      self.transformed_img = Image.new('RGBA', self.resized_img.size)
      self.transformed_img.paste(self.resized_img, None)
      if flip_hori:
        self.transformed_img = self.transformed_img.transpose(Image.FLIP_LEFT_RIGHT)
      if flip_vert:
        self.transformed_img = self.transformed_img.transpose(Image.FLIP_TOP_BOTTOM)
      self.tk_img = ImageTk.PhotoImage(self.transformed_img.rotate((-180.0 * self.rotation / math.pi), expand = True, fillcolor = '#00000000'))
      if not self.img_id:
        self.img_id = self.canvas.create_image(imgx, imgy, image = self.tk_img, anchor = tk.NW)
      else:
        self.canvas.coords(self.img_id, imgx, imgy)
        self.canvas.itemconfigure(self.img_id, image = self.tk_img)
        
  def load_image(self):
    try:
      self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
      print(f"image loaded from {self.img_url}")
    except:
      print(f"failed to load image from {self.img_url}")
      self.orig_img = None
    
  def set_url(self, url : str, local : bool = True) -> None:
    if self.url_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return
    
    if self.img_url != url:
      self.img_url = url
      self.url_strvar.set(self.img_url)
      self.load_image()
      
      self.redraw()
      
      self.url_changed |= local
      
  def move_to_front(self, under : int = None) -> None:
    last_id = self.move_id_to_front(self.img_id, under)
    return super().move_to_front(last_id)
  
  def move_to_back(self, above : int = None) -> None:
    last_id = self.move_id_to_back(self.img_id, above)
    return super().move_to_back(last_id)
  
  def queue_set_input_url(self, gui : 'Default_GUI') -> None:
    urlreq = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'file': self.img_url }})
    gui.connection.queue_request(urlreq)
    
    
  def update_info(self) -> None:
    newurl = self.url_strvar.get()
    
    if newurl != self.img_url:
      self.set_url(newurl)
      
    super().update_info()
      
  def setup_modify_url(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_url_label = ttk.Label(frame, text = "URL:")
    self.modify_url_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_url_entry = ttk.Entry(frame, textvariable = self.url_strvar)
    self.modify_url_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    super().setup_modify_ui(gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_url(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
    
    return super().setup_modify_ui(gui)

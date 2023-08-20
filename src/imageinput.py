import math
import tkinter as tk
from tkinter import ttk

import requests
import simpleobsws
from PIL import Image, ImageTk

import obs_object as obsobj


class ImageInput(obsobj.OBS_Object):
  img_url = ""
  img_id = None
  orig_img = None
  resized_img = None
  transformed_img = None
  tk_img = None
  
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
    
  def set_image_url(self, url : str) -> None:
    if self.img_url != url:
      try:
        self.img_url = url
        self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
        print(f"image loaded from {url}")
      except:
        print(f"failed to load image from {url}")
        self.orig_img = None
      self.redraw()
      
  def move_to_front(self, under : obsobj.OBS_Object = None) -> None:
    if self.img_id:
      if under:
        self.canvas.tag_raise(self.img_id, under)
      else:
        self.canvas.tag_raise(self.img_id)
        
    return super().move_to_front(self.img_id)
    
  def queue_update_req(self, gui : 'owg.OBS_WS_GUI') -> None:
    newname = self.modify_name_strvar.get()
    newurl = self.modify_url_strvar.get()
    
    if newurl != self.img_url:
      urlreq = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'file': self.modify_url_entry.get() }})
      gui.connection.queue_request(urlreq)
    if newname != self.source_name:
      namereq = simpleobsws.Request('SetInputName', { 'inputName': self.source_name, 'newInputName': self.modify_name_strvar.get()})
      gui.connection.queue_request(namereq)
      
  def setup_modify_url(self, gui : 'owg.OBS_WS_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_url_label = ttk.Label(frame, text = "URL:")
    self.modify_url_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_url_strvar = tk.StringVar(gui.root, self.img_url)
    self.modify_url_entry = ttk.Entry(frame, textvariable = self.modify_url_strvar)
    self.modify_url_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_modify_ui(self, gui : 'owg.OBS_WS_GUI') -> None:
    super().setup_modify_ui(gui)
    
    row = 0
    row = self.setup_modify_name(gui, gui.modifyframe, row)
    row = self.setup_modify_url(gui, gui.modifyframe, row)
    row = self.setup_update_button(gui, gui.modifyframe, row)
    row = self.setup_standard_buttons(gui, gui.modifyframe, row)
    
    return super().setup_modify_ui(gui)
  
import obswsgui as owg

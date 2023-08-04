from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import math

class Coords:
  x = 0
  y = 0
  
  def __init__(self, x = 0, y = 0):
    self.x = x
    self.y = y
    
  def __repr__(self):
    return f"({self.x}, {self.y})"
  
MOVE = 'move'
TOPLEFT = 'resize_tl'
TOPRIGHT = 'resize_tr'
BOTTOMLEFT = 'resize_bl'
BOTTOMRIGHT = 'resize_br'
LEFT = 'resize_l'
RIGHT = 'resize_r'
TOP = 'resize_t'
BOTTOM = 'resize_b'

def between(val : float, bound1 : float, bound2 : float, inclusive : bool = True):
  if inclusive:
    return (bound1 <= val <= bound2) if (bound1 < bound2) else (bound2 <= val <= bound1)
  else:
    return (bound1 < val < bound2) if (bound1 < bound2) else (bound2 < val < bound1)

class OBS_Object:
  x = 0.0
  y = 0.0
  width = 0.0
  height = 0.0
  source_width = 0.0
  source_height = 0.0
  
  xpx = 0
  ypx = 0
  wpx = 0
  hpx = 0
  
  last_xpx = 0
  last_ypx = 0
  last_wpx = 0
  last_hpx = 0
  
  source_name = ""
  scene_item_id = 0
  scene_item_index = 0
  bounds_type = ""
  
  scale = 1.0
  
  screen = None
  canvas = None
  
  rect_id = None
  text_id = None
  tl_grab_id = None
  tr_grab_id = None
  bl_grab_id = None
  br_grab_id = None
  
  img_url = ""
  img_id = None
  orig_img = None
  resized_img = None
  transformed_img = None
  tk_img = None
  
  line_width = 5
  selected = False
  was_selected = False
  
  grabber_radius = 5
  
  interactable = True
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : Canvas, screen, x : float, y : float, width : float, height : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.scene_item_id = scene_item_id
    self.scene_item_index = scene_item_index
    self.canvas = canvas
    self.screen = screen
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.source_width = source_width
    self.source_height = source_height
    self.bounds_type = bounds_type
    self.source_name = label
    self.interactable = interactable
    
  def __del__(self):
    if self.rect_id:
      self.canvas.delete(self.rect_id)
    if self.tl_grab_id:
      self.canvas.delete(self.tl_grab_id)
    if self.bl_grab_id:
      self.canvas.delete(self.bl_grab_id)
    if self.tr_grab_id:
      self.canvas.delete(self.tr_grab_id)
    if self.br_grab_id:
      self.canvas.delete(self.br_grab_id)
    if self.text_id:
      self.canvas.delete(self.text_id)
    if self.img_id:
      self.canvas.delete(self.img_id)
    
  def draw(self):
    new_scale = self.screen.scale
    
    self.xpx = self.screen.xpx + (self.x * new_scale)
    self.ypx = self.screen.ypx + (self.y * new_scale)
    self.wpx = self.width * new_scale
    self.hpx = self.height * new_scale
    x2px = self.xpx + self.wpx
    y2px = self.ypx + self.hpx
    
    if self.scale != new_scale or self.last_xpx != self.xpx or self.last_ypx != self.ypx or self.last_wpx != self.wpx or self.last_hpx != self.hpx or self.was_selected != self.selected:
      self.scale = new_scale
      
      gpx = math.ceil(self.grabber_radius * self.scale) + 1
      
      lw = math.ceil(self.line_width * self.scale) + 1
      
      c = "red" if self.selected else "black"
      
      if self.orig_img:
        imgx = self.xpx
        imgy = self.ypx
        imgw = round(self.wpx)
        imgh = round(self.hpx)
        flip_hori = False
        flip_vert = False
        
        if imgw == 0:
          imgw = 1
        if imgw < 0:
          imgw = abs(imgw) 
          imgx = imgx - imgw
          flip_hori = True
          
        if imgh == 0:
          imgh = 1
        if imgh < 0:
          imgh = abs(imgh)
          imgy = imgy - imgh
          flip_vert = True 
        
        self.resized_img = self.orig_img.resize((imgw, imgh))
        self.transformed_img = self.resized_img
        if flip_hori:
          self.transformed_img = self.transformed_img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_vert:
          self.transformed_img = self.transformed_img.transpose(Image.FLIP_TOP_BOTTOM)
        self.tk_img = ImageTk.PhotoImage(self.transformed_img)
        if not self.img_id:
          self.img_id = self.canvas.create_image(imgx, imgy, image = self.tk_img, anchor = NW)
        else:
          self.canvas.coords(self.img_id, imgx, imgy)
          self.canvas.itemconfigure(self.img_id, image = self.tk_img)
        
      if not self.rect_id:
        self.rect_id = self.canvas.create_rectangle(self.xpx, self.ypx, x2px, y2px, width = lw, outline = c)
      else:
        self.canvas.coords(self.rect_id, self.xpx, self.ypx, x2px, y2px)
        self.canvas.itemconfigure(self.rect_id, width = lw, outline = c)
      
      if self.interactable:
        if not self.tl_grab_id:
          self.tl_grab_id = self.canvas.create_oval(self.xpx - gpx, self.ypx - gpx, self.xpx + gpx, self.ypx + gpx, width = lw, outline = c)
        else:
          self.canvas.coords(self.tl_grab_id, self.xpx - gpx, self.ypx - gpx, self.xpx + gpx, self.ypx + gpx)
          self.canvas.itemconfigure(self.tl_grab_id, width = lw, outline = c)
      elif self.tl_grab_id:
        self.canvas.delete(self.tl_grab_id)
        self.tl_grab_id = None
        
      if self.interactable:
        if not self.bl_grab_id:
          self.bl_grab_id = self.canvas.create_oval(self.xpx - gpx, y2px - gpx, self.xpx + gpx, y2px + gpx, width = lw, outline = c)
        else:
          self.canvas.coords(self.bl_grab_id, self.xpx - gpx, y2px - gpx,     self.xpx + gpx, y2px + gpx)
          self.canvas.itemconfigure(self.bl_grab_id, width = lw, outline = c)
      elif self.bl_grab_id:
        self.canvas.delete(self.bl_grab_id)
        self.bl_grab_id = None
        
      if self.interactable:
        if not self.tr_grab_id:
          self.tr_grab_id = self.canvas.create_oval(x2px - gpx, self.ypx - gpx, x2px + gpx, self.ypx + gpx, width = lw, outline = c)
        else:
          self.canvas.coords(self.tr_grab_id, x2px - gpx, self.ypx - gpx, x2px + gpx, self.ypx + gpx)
          self.canvas.itemconfigure(self.tr_grab_id, width = lw, outline = c)
      elif self.tr_grab_id:
        self.canvas.delete(self.tr_grab_id)
        self.tr_grab_id = None
        
      if self.interactable:
        if not self.br_grab_id:
          self.br_grab_id = self.canvas.create_oval(x2px - gpx, y2px - gpx, x2px + gpx, y2px + gpx, width = lw, outline = c)
        else:
          self.canvas.coords(self.br_grab_id, x2px - gpx, y2px - gpx, x2px + gpx, y2px + gpx)
          self.canvas.itemconfigure(self.br_grab_id, width = lw, outline = c)
      elif self.br_grab_id:
        self.canvas.delete(self.br_grab_id)
        self.br_grab_id = None
      
      if not self.text_id:
        self.text_id = self.canvas.create_text(self.xpx + lw + 1, self.ypx + lw + 1, anchor = NW, text = self.source_name)
      else:
        self.canvas.coords(self.text_id, self.xpx + lw + 1, self.ypx + lw + 1)
        self.canvas.itemconfigure(self.text_id, anchor = NW, text = self.source_name)
      
      self.last_xpx = self.xpx
      self.last_ypx = self.ypx
      self.last_wpx = self.wpx
      self.last_hpx = self.hpx
      self.was_selected = self.selected
    
  def contains(self, coords : Coords):
    x_inside = between(coords.x, self.x, self.x + self.width)
    y_inside = between(coords.y, self.y, self.y + self.height)
    return x_inside and y_inside
  
  def set_image(self, url : str):
    try:
      self.img_url = url
      self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
      print(f"image loaded from {url}")
    except:
      print(f"failed to load image from {url}")
      self.orig_img = None
  
  def move_or_resize(self, coords : Coords, zone : int = 10):
    if not self.interactable:
      return None
    
    leftside = abs(coords.x - self.x) < zone
    rightside = abs(coords.x - (self.x + self.width)) < zone
    topside = abs(coords.y - self.y) < zone
    bottomside = abs(coords.y - (self.y + self.height)) < zone
    
    
    x_inside = between(coords.x, self.x, self.x + self.width)
    y_inside = between(coords.y, self.y, self.y + self.height)
    
    if leftside:
      if topside:
        return TOPLEFT
      elif bottomside:
        return BOTTOMLEFT
      elif y_inside:
        return LEFT
    elif rightside:
      if topside:
        return TOPRIGHT
      elif bottomside:
        return BOTTOMRIGHT
      elif y_inside:
        return RIGHT
    elif topside and x_inside:
      return TOP
    elif bottomside and x_inside:
      return BOTTOM
    else:
      if self.contains(coords):
        return MOVE
      
    return None
  
  def move_to_front(self, under = None):
    if self.img_id:
      if under:
        self.canvas.tag_raise(self.img_id, under.text_id)
      else:
        self.canvas.tag_raise(self.img_id)
    if self.rect_id:
      self.canvas.tag_raise(self.rect_id, self.img_id)
    if self.tl_grab_id:
      self.canvas.tag_raise(self.tl_grab_id, self.rect_id)
    if self.tr_grab_id:
      self.canvas.tag_raise(self.tr_grab_id, self.tl_grab_id)
    if self.bl_grab_id:
      self.canvas.tag_raise(self.bl_grab_id, self.tr_grab_id)
    if self.br_grab_id:
      self.canvas.tag_raise(self.br_grab_id, self.bl_grab_id)
    if self.text_id:
      self.canvas.tag_raise(self.text_id, self.br_grab_id)
    
class ScreenObj(OBS_Object):
  anchor = 'center'
  
  def __init__(self, canvas : Canvas, anchor, width : float, height : float, label : str = ""):
    self.canvas = canvas
    self.screen = None
    self.anchor = anchor
    self.x = 0
    self.y = 0
    self.scale = 1.0
    self.width = width
    self.height = height
    self.label = label
    
  def draw(self):
    self.scale = 1.0 / max(self.height / (self.canvas.winfo_height() * 2.0 / 3.0), self.width / (self.canvas.winfo_width() * 2.0 / 3.0))
    
    lw = math.ceil(self.line_width * self.scale) + 1
    
    self.xpx = 0
    self.ypx = 0
    self.wpx = self.width  * self.scale
    self.hpx = self.height * self.scale
    
    if (self.anchor == 'center'):
      self.xpx = (self.canvas.winfo_width() - self.wpx) / 2
      self.ypx = (self.canvas.winfo_height() - self.hpx) / 2
      x2_pixel = self.xpx + self.wpx
      y2_pixel = self.ypx + self.hpx
    
    if not self.rect_id:
      self.rect_id = self.canvas.create_rectangle(self.xpx, self.ypx, x2_pixel, y2_pixel, width = lw)
    else:
      self.canvas.coords(self.rect_id, self.xpx, self.ypx, x2_pixel, y2_pixel)
      self.canvas.itemconfigure(self.rect_id, width = lw)
      
    if not self.text_id:
      self.text_id = self.canvas.create_text(self.xpx, self.ypx - 1, anchor = SW, text = self.label)
    else:
      self.canvas.coords(self.text_id, self.xpx, self.ypx - 1)
      self.canvas.itemconfigure(self.text_id, anchor = SW, text = self.label)
    
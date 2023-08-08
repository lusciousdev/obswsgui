from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import math
from enum import Enum
import simpleobsws

class Coords:
  x = 0
  y = 0
  
  def __init__(self, x = 0, y = 0):
    self.x = x
    self.y = y
    
  def __repr__(self):
    return f"({self.x}, {self.y})"
  
class InputKind(Enum):
  IMAGE_SOURCE = 'image_source'
  COLOR_SOURCE = 'color_source_v3'
  SLIDESHOW = 'slideshow'
  BROWSER_SOURCE = 'browser_source'
  FFMPEG_SOURCE = 'ffmpeg_source'
  TEXT_SOURCE_WINDOWS = 'text_gdiplus_v2'
  TEXT_SOURCE_OTHER = 'text_ft_source_v2'
  VLC_SOURCE = 'vlc_source'
  MONITOR_CAPTURE = 'monitor_capture'
  WINDOW_CAPTURE = 'window_capture'
  GAME_CAPTURE = 'game_capture'
  DSHOW_INPUT = 'dshow_input'
  WASAPI_INPUT_CAPTURE = 'wasapi_input_capture'
  WASAPI_OUTPUT_CAPTURE = 'wasapi_output_capture'
  WASAPI_PROCESS_OUTPUT_CAPTURE = 'wasapi_process_output_capture'
  
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
  
  x1px = 0
  y1px = 0
  x2px = 0
  y2px = 0
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
  grabber_ids = None
  
  line_width = 5
  selected = False
  was_selected = False
  
  grabber_radius = 5
  
  interactable = True
  
  default_color  = "#efeff1"
  selected_color = "#fab4ff"
  
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
    for id in self.grabber_ids:
      self.canvas.delete(id)
    if self.text_id:
      self.canvas.delete(self.text_id)
      
  def calculate_canvas_pos(self):
    self.scale = self.screen.scale
    
    self.x1px = self.screen.xpx + (self.x * self.scale)
    self.y1px = self.screen.ypx + (self.y * self.scale)
    self.wpx = self.width * self.scale
    self.hpx = self.height * self.scale
    self.x2px = self.x1px + self.wpx
    self.y2px = self.y1px + self.hpx
    
  def draw(self):
    self.calculate_canvas_pos()
    
    if self.last_xpx != self.x1px or self.last_ypx != self.y1px or self.last_wpx != self.wpx or self.last_hpx != self.hpx or self.was_selected != self.selected:
      gpx = math.ceil(self.grabber_radius * self.scale) + 1
      
      lw = math.ceil(self.line_width * self.scale) + 1
      
      c = self.selected_color if self.selected else self.default_color
        
      if not self.rect_id:
        self.rect_id = self.canvas.create_rectangle(self.x1px, self.y1px, self.x2px, self.y2px, width = lw, outline = c)
      else:
        self.canvas.coords(self.rect_id, self.x1px, self.y1px, self.x2px, self.y2px)
        self.canvas.itemconfigure(self.rect_id, width = lw, outline = c)
      
      if self.interactable:
        if not self.grabber_ids:
          tl = self.canvas.create_oval(self.x1px - gpx, self.y1px - gpx, self.x1px + gpx, self.y1px + gpx, width = lw, outline = c)
          bl = self.canvas.create_oval(self.x1px - gpx, self.y2px - gpx, self.x1px + gpx, self.y2px + gpx, width = lw, outline = c)
          tr = self.canvas.create_oval(self.x2px - gpx, self.y1px - gpx, self.x2px + gpx, self.y1px + gpx, width = lw, outline = c)
          br = self.canvas.create_oval(self.x2px - gpx, self.y2px - gpx, self.x2px + gpx, self.y2px + gpx, width = lw, outline = c)
          
          self.grabber_ids = [tl, bl, tr, br]
        else:
          for id in self.grabber_ids:
            self.canvas.itemconfigure(id, width = lw, outline = c)
          
          self.canvas.coords(self.grabber_ids[0], self.x1px - gpx, self.y1px - gpx, self.x1px + gpx, self.y1px + gpx)
          self.canvas.coords(self.grabber_ids[1], self.x1px - gpx, self.y2px - gpx, self.x1px + gpx, self.y2px + gpx)
          self.canvas.coords(self.grabber_ids[2], self.x2px - gpx, self.y1px - gpx, self.x2px + gpx, self.y1px + gpx)
          self.canvas.coords(self.grabber_ids[3], self.x2px - gpx, self.y2px - gpx, self.x2px + gpx, self.y2px + gpx)
      elif self.grabber_ids:
        for id in self.grabber_ids:
          self.canvas.delete(id)
        self.grabber_ids = None
      
      if not self.text_id:
        self.text_id = self.canvas.create_text(self.x1px, self.y1px - lw, anchor = SW, text = f"{self.source_name} ({self.scene_item_id})", fill = c)
      else:
        self.canvas.coords(self.text_id, self.x1px, self.y1px - lw)
        self.canvas.itemconfigure(self.text_id, anchor = SW, text = f"{self.source_name} ({self.scene_item_id})", fill = c)
      
      self.last_xpx = self.x1px
      self.last_ypx = self.y1px
      self.last_wpx = self.wpx
      self.last_hpx = self.hpx
      self.was_selected = self.selected
    
  def contains(self, coords : Coords):
    x_inside = between(coords.x, self.x, self.x + self.width)
    y_inside = between(coords.y, self.y, self.y + self.height)
    return x_inside and y_inside
  
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
    if self.rect_id:
      if under:
        self.canvas.tag_raise(self.rect_id, under)
      else:
        self.canvas.tag_raise(self.rect_id)
    if self.grabber_ids:
      for id in self.grabber_ids:
        self.canvas.tag_raise(id, self.rect_id)
    if self.text_id:
      self.canvas.tag_raise(self.text_id, self.grabber_ids[0])
    
  def queue_move_to_front(self, gui):
    index_req = simpleobsws.Request('SetSceneItemIndex', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id, 'sceneItemIndex': gui.scene_items[0].scene_item_index})
    gui.requests_queue.append(index_req)
      
  def setup_modify_ui(self, gui):
    return None
    
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
      self.rect_id = self.canvas.create_rectangle(self.xpx, self.ypx, x2_pixel, y2_pixel, width = lw, outline = self.default_color)
    else:
      self.canvas.coords(self.rect_id, self.xpx, self.ypx, x2_pixel, y2_pixel)
      self.canvas.itemconfigure(self.rect_id, width = lw)
      
    if not self.text_id:
      self.text_id = self.canvas.create_text(self.xpx, self.ypx - 1, anchor = SW, text = self.label, fill = self.default_color)
    else:
      self.canvas.coords(self.text_id, self.xpx, self.ypx - 1)
      self.canvas.itemconfigure(self.text_id, anchor = SW, text = self.label)
      
class ImageInput(OBS_Object):
  img_url = ""
  img_id = None
  orig_img = None
  resized_img = None
  transformed_img = None
  tk_img = None
  
  def __del__(self):
    super().__del__()
    if self.img_id:
      self.canvas.delete(self.img_id)
  
  def draw(self):
    self.calculate_canvas_pos()
    
    if self.last_xpx != self.x1px or self.last_ypx != self.y1px or self.last_wpx != self.wpx or self.last_hpx != self.hpx or self.was_selected != self.selected:
      if self.orig_img:
        imgx = self.x1px
        imgy = self.y1px
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
        
    return super().draw()
    
  
  def set_image(self, url : str):
    try:
      self.img_url = url
      self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
      print(f"image loaded from {url}")
    except:
      print(f"failed to load image from {url}")
      self.orig_img = None
      
  def move_to_front(self, under = None):
    if self.img_id:
      if under:
        self.canvas.tag_raise(self.img_id, under.text_id)
      else:
        self.canvas.tag_raise(self.img_id)
        
    return super().move_to_front(self.img_id)
    
  def queue_update_image_req(self, gui):
    newname = self.modify_name_strvar.get()
    newurl = self.modify_url_strvar.get()
    
    if newurl != self.img_url:
      urlreq = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'file': self.modify_url_entry.get() }})
      gui.requests_queue.append(urlreq)
    if newname != self.source_name:
      namereq = simpleobsws.Request('SetInputName', { 'inputName': self.source_name, 'newInputName': self.modify_name_strvar.get()})
      gui.requests_queue.append(namereq)
    
  def setup_update_image_dialog(self, gui):
    self.update_image_dialog = Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.update_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.update_image_dialog.protocol("WM_DELETE_WINDOW", self.update_image_dialog.destroy)
    
    self.update_image_frame = ttk.Frame(self.update_image_dialog, padding = "12 12 12 12")
    self.update_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    
    self.update_image_name_label = ttk.Label(self.update_image_frame, text = f"Update name and/or URL for \"{self.source_name} ({self.scene_item_id})\"?")
    self.update_image_name_label.grid(column = 0, columnspan = 2, row = 0, sticky = (W, E))
    self.update_image_warn_label = ttk.Label(self.update_image_frame, text = f"(this will affect all inputs with the same name)")
    self.update_image_warn_label.grid(column = 0, columnspan = 2, row = 1, sticky = (W, E))
    
    def updatefunc():
      self.queue_update_image_req(gui)
      self.update_image_dialog.destroy()
      
    self.update_image_submit = ttk.Button(self.update_image_frame, text = "Yes", command = updatefunc)
    self.update_image_submit.grid(column = 0, row = 2, sticky = (W, E))
  
    self.update_image_cancel = ttk.Button(self.update_image_frame, text = "No", command = self.update_image_dialog.destroy)
    self.update_image_cancel.grid(column = 1, row = 2, sticky = (W, E))
    
  def queue_duplicate_image_req(self, gui):
    img_req = simpleobsws.Request('DuplicateSceneItem', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id})
    gui.requests_queue.append(img_req)
    
  def setup_duplicate_image_dialog(self, gui):
    self.dup_image_dialog = Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.dup_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.dup_image_dialog.protocol("WM_DELETE_WINDOW", self.dup_image_dialog.destroy)
    
    self.dup_image_frame = ttk.Frame(self.dup_image_dialog, padding = "12 12 12 12")
    self.dup_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.dup_image_frame.grid_columnconfigure(0, weight = 1)
    
    self.dup_image_name_label = ttk.Label(self.dup_image_frame, text = f"Duplicate \"{self.source_name} ({self.scene_item_id})\"?")
    self.dup_image_name_label.grid(column = 0, columnspan = 2, row = 0, sticky = (W, E))
    
    def dup():
      self.queue_duplicate_image_req(gui)
      self.dup_image_dialog.destroy()
      
    self.dup_image_submit = ttk.Button(self.dup_image_frame, text = "Yes", command = dup)
    self.dup_image_submit.grid(column = 0, row = 1, sticky = (W, E))
  
    self.dup_image_cancel = ttk.Button(self.dup_image_frame, text = "No", command = self.dup_image_dialog.destroy)
    self.dup_image_cancel.grid(column = 1, row = 1, sticky = (W, E))
    
  def queue_delete_image_req(self, gui):
    del_req = simpleobsws.Request('RemoveSceneItem', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id })
    gui.requests_queue.append(del_req)
    
  def setup_delete_image_dialog(self, gui):
    self.del_image_dialog = Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.del_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.del_image_dialog.protocol("WM_DELETE_WINDOW", self.del_image_dialog.destroy)
    
    self.del_image_frame = ttk.Frame(self.del_image_dialog, padding = "12 12 12 12")
    self.del_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.del_image_frame.grid_columnconfigure(0, weight = 1)
    
    self.del_image_prompt = ttk.Label(self.del_image_frame, text = f"Are you sure you want to delete \"{self.source_name} ({self.scene_item_id})\"?")
    self.del_image_prompt.grid(column = 0, columnspan = 2, row = 0, sticky = (W, E))
    
    def delimg():
      self.queue_delete_image_req(gui)
      self.del_image_dialog.destroy()
    
    self.del_image_submit = ttk.Button(self.del_image_frame, text = "Yes", command = delimg)
    self.del_image_submit.grid(column = 0, row = 1, sticky = E)
    self.del_image_cancel = ttk.Button(self.del_image_frame, text = "No", command = self.del_image_dialog.destroy)
    self.del_image_cancel.grid(column = 1, row = 1, sticky = E)
  
  def setup_modify_ui(self, gui):
    gui.modifyframe.columnconfigure(0, weight = 1)
    
    self.modify_name_label = ttk.Label(gui.modifyframe, text = "Name:")
    self.modify_name_label.grid(column = 0, row = 0, sticky = W)
    
    self.modify_name_strvar = StringVar(gui.root, self.source_name)
    self.modify_name_entry = ttk.Entry(gui.modifyframe, textvariable=self.modify_name_strvar)
    self.modify_name_entry.grid(column = 0, row = 1, sticky = (W, E), pady = (0, 5))
    
    self.modify_url_label = ttk.Label(gui.modifyframe, text = "URL:")
    self.modify_url_label.grid(column = 0, row = 2, sticky = W)
    
    self.modify_url_strvar = StringVar(gui.root, self.img_url)
    self.modify_url_entry = ttk.Entry(gui.modifyframe, textvariable = self.modify_url_strvar)
    self.modify_url_entry.grid(column = 0, row = 3, sticky = (W, E), pady = (0, 5))
    
    self.update_button = ttk.Button(gui.modifyframe, text = "Update", command = lambda: self.setup_update_image_dialog(gui))
    self.update_button.grid(column = 0, row = 4, sticky = (W, E), pady = (0, 5))
    
    self.dupimage = ttk.Button(gui.modifyframe, text = "Duplicate", command = lambda: self.setup_duplicate_image_dialog(gui))
    self.dupimage.grid(column = 0, row = 5, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Delete", command = lambda: self.setup_delete_image_dialog(gui))
    self.deleteimage.grid(column = 0, row = 6, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = 7, sticky = (W, E), pady = (0, 5))
    
    return super().setup_modify_ui(gui)
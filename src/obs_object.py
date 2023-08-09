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
  selected = False
  
  x1px = 0
  y1px = 0
  x2px = 0
  y2px = 0
  wpx = 0
  hpx = 0
  
  source_name = ""
  scene_item_id = 0
  scene_item_index = 0
  bounds_type = ""
  
  scale = 1.0
  
  screen = None
  canvas = None
  
  rect_id = None
  item_label_id = None
  grabber_ids = None
  
  line_width = 5
  grabber_radius = 6
  
  interactable = True
  
  default_color  = "#efeff1"
  selected_color = "#fab4ff"
  
  changed = False
  
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
    
    self.rect_id = self.canvas.create_rectangle(0, 0, 0, 0, width = self.line_width, outline = self.default_color)
    
    if self.interactable:
      tl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      bl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      tr = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      br = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      
      self.grabber_ids = [tl, bl, tr, br]
    
    self.item_label_id = self.canvas.create_text(0, 0, anchor = SW, text = f"{self.source_name} ({self.scene_item_id})", fill = self.default_color)
    
    self.redraw()
    
  def __del__(self):
    if self.rect_id:
      self.canvas.delete(self.rect_id)
    for id in self.grabber_ids:
      self.canvas.delete(id)
    if self.item_label_id:
      self.canvas.delete(self.item_label_id)
      
  def calculate_canvas_pos(self):
    self.scale = self.screen.scale
    
    self.x1px = self.screen.x1px + (self.x * self.scale)
    self.y1px = self.screen.y1px + (self.y * self.scale)
    self.wpx = self.width * self.scale
    self.hpx = self.height * self.scale
    self.x2px = self.x1px + self.wpx
    self.y2px = self.y1px + self.hpx
    
  def get_linewidth(self):
    return math.ceil(self.line_width * self.scale) + 1
  
  def get_grabberradius(self):
    return math.ceil(self.grabber_radius * self.scale) + 1
  
  def get_color(self):
    return self.selected_color if self.selected else self.default_color
    
  def set_transform(self, x = None, y = None, w = None, h = None, local = True):
    x = self.x if x is None else x
    y = self.y if y is None else y
    w = self.width if w is None else w
    h = self.height if h is None else h
    
    if self.x != x or self.y != y or self.width != w or self.height != h:
      self.x = x
      self.y = y
      self.width = w
      self.height = h
      
      self.changed = local
      self.redraw()
      
  def set_selected(self, selected):
    if self.selected != selected:
      self.selected = selected
      
      c = self.get_color()
      self.canvas.itemconfigure(self.item_label_id, fill = c)
      self.canvas.itemconfigure(self.rect_id, outline = c)
      for id in self.grabber_ids:
        self.canvas.itemconfigure(id, fill = c)
    
  def set_interactable(self, interactable):
    if self.interactable != interactable:
      self.interactable = interactable
      
      if self.interactable:
        self.calculate_canvas_pos()
        c = self.get_color()
        lw = self.get_linewidth()
        gpx = self.get_grabberradius()
        tl = self.canvas.create_oval(self.x1px - gpx, self.y1px - gpx, self.x1px + gpx, self.y1px + gpx, width = lw, outline = "", fill = c)
        bl = self.canvas.create_oval(self.x1px - gpx, self.y2px - gpx, self.x1px + gpx, self.y2px + gpx, width = lw, outline = "", fill = c)
        tr = self.canvas.create_oval(self.x2px - gpx, self.y1px - gpx, self.x2px + gpx, self.y1px + gpx, width = lw, outline = "", fill = c)
        br = self.canvas.create_oval(self.x2px - gpx, self.y2px - gpx, self.x2px + gpx, self.y2px + gpx, width = lw, outline = "", fill = c)
        
        self.grabber_ids = [tl, bl, tr, br]
      else:
        for id in self.grabber_ids:
          self.canvas.delete(id)
        self.grabber_ids = None
    
  def set_source_name(self, source_name):
    if self.source_name != source_name:
      self.source_name = source_name
      self.canvas.itemconfigure(self.item_label_id, text = f"{self.source_name} ({self.scene_item_id})")
      
  def canvas_configure(self, event = None):
    self.scale = self.screen.scale
    self.redraw()
      
  def redraw(self):
    self.calculate_canvas_pos()
    gpx = self.get_grabberradius()
    lw = self.get_linewidth()
    
    self.canvas.coords(self.rect_id, self.x1px, self.y1px, self.x2px, self.y2px)
    self.canvas.itemconfigure(self.rect_id, width = lw)
      
    if self.interactable:
      for id in self.grabber_ids:
        self.canvas.itemconfigure(id, width = lw)
      
      self.canvas.coords(self.grabber_ids[0], self.x1px - gpx, self.y1px - gpx, self.x1px + gpx, self.y1px + gpx)
      self.canvas.coords(self.grabber_ids[1], self.x1px - gpx, self.y2px - gpx, self.x1px + gpx, self.y2px + gpx)
      self.canvas.coords(self.grabber_ids[2], self.x2px - gpx, self.y1px - gpx, self.x2px + gpx, self.y1px + gpx)
      self.canvas.coords(self.grabber_ids[3], self.x2px - gpx, self.y2px - gpx, self.x2px + gpx, self.y2px + gpx)
      
    self.canvas.coords(self.item_label_id, self.x1px, self.y1px - lw)
    
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
    if self.item_label_id:
      self.canvas.tag_raise(self.item_label_id, self.rect_id if not self.grabber_ids else self.grabber_ids[0])
    
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
    
    self.rect_id = self.canvas.create_rectangle(0, 0, 0, 0, width = self.line_width, outline = self.default_color)
    self.item_label_id = self.canvas.create_text(0, 0, anchor = SW, text = self.label, fill = self.default_color)
    
  def canvas_configure(self, event = None):
    self.scale = 1.0 / max(self.height / (self.canvas.winfo_height() * 2.0 / 3.0), self.width / (self.canvas.winfo_width() * 2.0 / 3.0))
    self.redraw()
    
  def redraw(self):
    lw = self.get_linewidth()
    
    self.x1px = 0
    self.y1px = 0
    self.wpx = self.width  * self.scale
    self.hpx = self.height * self.scale
    
    if (self.anchor == 'center'):
      self.x1px = (self.canvas.winfo_width() - self.wpx) / 2
      self.y1px = (self.canvas.winfo_height() - self.hpx) / 2
      self.x2px = self.x1px + self.wpx
      self.y2px = self.y1px + self.hpx
    
    self.canvas.coords(self.rect_id, self.x1px, self.y1px, self.x2px, self.y2px)
    self.canvas.itemconfigure(self.rect_id, width = lw)
      
    self.canvas.coords(self.item_label_id, self.x1px, self.y1px - 1)
    self.canvas.itemconfigure(self.item_label_id, anchor = SW, text = self.label)
      
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
  
  def redraw(self):
    super().redraw()
    
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
    
  def set_image_url(self, url : str):
    try:
      if self.img_url != url:
        self.img_url = url
        self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
        self.redraw()
        print(f"image loaded from {url}")
    except:
      print(f"failed to load image from {url}")
      self.orig_img = None
      
  def move_to_front(self, under = None):
    if self.img_id:
      if under:
        self.canvas.tag_raise(self.img_id, under)
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
  
class TextInput(OBS_Object):
  text = ""
  text_id = None
  
  vertical = False
  color = "#fff"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : Canvas, screen, x : float, y : float, width : float, height : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, source_width, source_height, bounds_type, label, interactable)
    
    self.text_id = self.canvas.create_text(self.x1px, self.y1px, fill = self.default_color, text = self.text, anchor = NW)
    
  def set_text(self, text):
    if self.text != text:
      self.text = text
      self.canvas.itemconfigure(self.text_id, text = self.text)
      
  def set_vertical(self, vertical):
    if self.vertical != vertical:
      self.vertical = vertical
      self.canvas.itemconfigure(self.text_id, angle = 0 if not self.vertical else 270, anchor = NW if not self.vertical else SW)
      
  def redraw(self):
    super().redraw()
    
    if self.text_id:
      self.canvas.coords(self.text_id, self.x1px, self.y1px)
    
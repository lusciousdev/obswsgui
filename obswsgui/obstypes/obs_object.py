import enum
import math
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
  from ..ui.defaultgui import Default_GUI

import simpleobsws

from ..util.geometryutil import (
  Coords,
  Polygon,
  distance,
  distance_from_segment,
  point_in_polygon
)

class InputKind(enum.Enum):
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
  
class ModifyType(enum.IntFlag):
  NONE   = 0
  MOVE   = enum.auto()
  LEFT   = enum.auto()
  RIGHT  = enum.auto()
  TOP    = enum.auto()
  BOTTOM = enum.auto()
  ROTATE = enum.auto()

def between(val : float, bound1 : float, bound2 : float, inclusive : bool = True):
  if inclusive:
    return (bound1 <= val <= bound2) if (bound1 < bound2) else (bound2 <= val <= bound1)
  else:
    return (bound1 < val < bound2) if (bound1 < bound2) else (bound2 < val < bound1)
  
def flatten(l : list):
  return [item for sublist in l for item in sublist]

class OBS_Object:
  x             : float = 0.0
  y             : float = 0.0
  width         : float = 0.0
  height        : float = 0.0
  rotation      : float = 0.0 # in radians
  source_width  : float = 0.0
  source_height : float = 0.0
  
  selected : bool = False
  
  polygon : Polygon = Polygon()
  
  wpx : float = 0.0
  hpx : float = 0.0
  
  source_name      : str = ""
  last_source_name : str = ""
  source_name_changed : bool = False

  scene_item_id    : int = -1
  scene_item_index : int = -1
  bounds_type      : str = ""
  
  scale : float = 1.0
  
  screen : 'OBS_Object' = None
  canvas : tk.Canvas    = None
  
  rect_id            : int       = None
  item_label_id      : int       = None
  rotator_grabber_id : int       = None
  rotator_line_id    : int       = None
  grabber_ids        : List[int] = None
  
  rotator_dist : float = 40
  rotator_grabber_pos : Coords = Coords()
  
  line_width : float = 4
  grabber_radius : float = 8
  
  interactable : bool = True
  
  default_color  : str = "#efeff1"
  selected_color : str = "#fab4ff"
  
  trans_changed : bool = False
  
  @staticmethod
  def description():
    return "OBS Object"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : tk.Canvas, screen, x : float, y : float, width : float, height : float, rotation : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.scene_item_id = scene_item_id
    self.scene_item_index = scene_item_index
    self.canvas = canvas
    self.screen = screen
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.rotation = rotation
    self.source_width = source_width
    self.source_height = source_height
    self.bounds_type = bounds_type
    self.source_name = label
    self.interactable = interactable
    
    self.polygon = Polygon([0, 0], [0, 0], [0, 0], [0, 0])
    
    self.rect_id = self.canvas.create_polygon(self.polygon.to_array(), width = self.line_width, outline = self.default_color, fill = '')
    
    if self.interactable:
      tl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      bl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      tr = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      br = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      
      self.grabber_ids = [tl, bl, tr, br]
      
      self.rotator_grabber_id = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      self.rotator_line_id    = self.canvas.create_line(0, 0, 0, 0, width = self.line_width, fill = self.default_color)
    
    self.item_label_id = self.canvas.create_text(0, 0, anchor = tk.SW, text = f"{self.source_name} ({self.scene_item_id})", fill = self.default_color, angle = 0)
    
    self.name_strvar = tk.StringVar(self.canvas, self.source_name)
    
    self.redraw()
    
  def update(self, qui : 'Default_GUI') -> None:
    None
    
  def send_necessary_data(self, gui : 'Default_GUI') -> None:
    if self.source_name_changed:
      self.queue_set_input_name(gui)
      self.source_name_changed = False
    if self.trans_changed:
      self.queue_set_item_transform(gui)
      self.trans_changed = False
    
  def remove_from_canvas(self) -> None:
    if self.rect_id:
      self.canvas.delete(self.rect_id)
      self.rect_id = None
    if self.grabber_ids:
      for id in self.grabber_ids:
        self.canvas.delete(id)
      self.grabber_ids = None
    if self.item_label_id:
      self.canvas.delete(self.item_label_id)
      self.item_label_id = None
    if self.rotator_grabber_id:
      self.canvas.delete(self.rotator_grabber_id)
      self.rotator_grabber_id = None
    if self.rotator_line_id:
      self.canvas.delete(self.rotator_line_id)
      self.rotator_line_id = None
      
  def add_to_canvas(self) -> None:
    if self.rect_id is None:
      self.rect_id = self.canvas.create_polygon(self.polygon.to_array(), width = self.line_width, outline = self.default_color, fill = '')
    
    if self.interactable:
      if self.grabber_ids is None:
        tl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
        bl = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
        tr = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
        br = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
        
        self.grabber_ids = [tl, bl, tr, br]
        
      if self.rotator_grabber_id is None:
        self.rotator_grabber_id = self.canvas.create_oval(0, 0, 0, 0, width = self.line_width, outline = "", fill = self.default_color)
      if self.rotator_line_id is None:
        self.rotator_line_id    = self.canvas.create_line(0, 0, 0, 0, width = self.line_width, fill = self.default_color)
    
    if self.item_label_id is None:
      self.item_label_id = self.canvas.create_text(0, 0, anchor = tk.SW, text = f"{self.source_name} ({self.scene_item_id})", fill = self.default_color, angle = 0)
      
  def calculate_canvas_pos(self) -> None:
    self.scale = self.screen.scale
    
    screenx = self.screen.polygon.point(0).x
    screeny = self.screen.polygon.point(0).y
    self.polygon.point(0).x = screenx + (self.x * self.scale)
    self.polygon.point(0).y = screeny + (self.y * self.scale)
    
    self.wpx = self.width * self.scale
    self.hpx = self.height * self.scale
    
    diag_length = math.sqrt(math.pow(self.wpx, 2) + math.pow(self.hpx, 2))
    rect_angle = Coords(self.wpx, self.hpx).angle()
    
    self.polygon.point(1).x = self.polygon.point(0).x + self.wpx * math.cos(self.rotation)
    self.polygon.point(1).y = self.polygon.point(0).y + self.wpx * math.sin(self.rotation)
    
    self.polygon.point(2).x = self.polygon.point(0).x + diag_length * math.cos(self.rotation + rect_angle)
    self.polygon.point(2).y = self.polygon.point(0).y + diag_length * math.sin(self.rotation + rect_angle)
    
    self.polygon.point(3).x = self.polygon.point(0).x - self.hpx * math.cos((math.pi / 2) - self.rotation)
    self.polygon.point(3).y = self.polygon.point(0).y + self.hpx * math.sin((math.pi / 2) - self.rotation)
    
  def get_linewidth(self):
    return max(2, math.ceil(self.line_width * self.scale))
  
  def get_grabberradius(self):
    return max(2, math.ceil(self.grabber_radius * self.scale))
  
  def get_rotatordist(self):
    return max(15, math.ceil(self.rotator_dist * self.scale))
  
  def get_color(self):
    return self.selected_color if self.selected else self.default_color
        
  def queue_set_item_transform(self, gui : 'Default_GUI') -> None:
    scale_x = 1.0 if self.source_width == 0.0 else self.width / self.source_width
    scale_y = 1.0 if self.source_height == 0.0 else self.height / self.source_height
    rot = (180.0 * self.rotation / math.pi) % 360.0
    if self.bounds_type == 'OBS_BOUNDS_SCALE_INNER':
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id, 'sceneItemTransform': { 'positionX': self.x, 'positionY': self.y, 'boundsWidth': self.width, 'boundsHeight': self.height, 'rotation': rot }})
    else:
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id, 'sceneItemTransform': { 'positionX': self.x, 'positionY': self.y, 'scaleX': scale_x, 'scaleY': scale_y, 'rotation': rot }})
      
    gui.connection.queue_request(tf_req)
    
  def set_transform(self, x = None, y = None, w = None, h = None, rot = None, local = True):
    if self.trans_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return
    
    x = self.x if x is None else x
    y = self.y if y is None else y
    w = self.width if w is None else w
    h = self.height if h is None else h
    rot = self.rotation if rot is None else rot
    
    if self.x != x or self.y != y or self.width != w or self.height != h or self.rotation != rot:
      self.x = x
      self.y = y
      self.width = w
      self.height = h
      self.rotation = rot
      
      self.trans_changed |= local
      self.redraw()
      
  def set_selected(self, selected : bool) -> None:
    if self.selected != selected:
      self.selected = selected
      
      c = self.get_color()
      self.canvas.itemconfigure(self.item_label_id, fill = c)
      self.canvas.itemconfigure(self.rect_id, outline = c)
      for id in self.grabber_ids:
        self.canvas.itemconfigure(id, fill = c)
      self.canvas.itemconfigure(self.rotator_grabber_id, fill = c)
      self.canvas.itemconfigure(self.rotator_line_id, fill = c)
    
  def set_interactable(self, interactable : bool) -> None:
    if self.interactable != interactable:
      self.interactable = interactable
      
      if self.interactable:
        self.calculate_canvas_pos()
        c = self.get_color()
        lw = self.get_linewidth()
        gpx = self.get_grabberradius()
        self.grabber_ids = []
        for coords in self.polygon.points():
          grabber = self.canvas.create_oval(coords.x - gpx, coords.y - gpx, coords.x + gpx, coords.y + gpx, width = lw, outline = "", fill = c)
          self.grabber_ids.append(grabber)
        
        top_middle = (self.polygon.point(0) + self.polygon.point(1)) / 2.0
        rpx = self.get_rotatordist()
        
        inter_pos = Coords(0, math.copysign(rpx, self.hpx))
        inter_pos.rotate(self.rotation)
        self.rotator_grabber_pos = top_middle - inter_pos
        
        self.rotator_grabber_id = self.canvas.create_oval(self.rotator_grabber_pos.x - gpx, self.rotator_grabber_pos.y - gpx, self.rotator_grabber_pos.x + gpx, self.rotator_grabber_pos.y + gpx, width = lw, outline = "", fill = c)
        self.rotator_line_id = self.canvas.create_line(top_middle.x, top_middle.y, self.rotator_grabber_pos.x, self.rotator_grabber_pos.y, width = lw, outline = "", fill = c)
      else:
        for id in self.grabber_ids:
          self.canvas.delete(id)
        self.grabber_ids = None
        
        self.canvas.delete(self.rotator_grabber_id)
        self.canvas.delete(self.rotator_line_id)
        self.rotator_grabber_id = None
        self.rotator_line_id = None
        
  def set_scene_item_id(self, scene_item_id : int) -> None:
    if self.scene_item_id != scene_item_id:
      self.scene_item_id = scene_item_id
      self.canvas.itemconfigure(self.item_label_id, text = f"{self.source_name} ({self.scene_item_id})")
    
  def set_source_name(self, source_name : str, local : bool = True) -> None:
    if self.source_name_changed and not local:
      # ignore network updates while we are still waiting to send our state
      return
    
    if self.source_name != source_name:
      self.last_source_name = self.source_name
      self.source_name = source_name
      self.name_strvar.set(self.source_name)
      self.canvas.itemconfigure(self.item_label_id, text = f"{self.source_name} ({self.scene_item_id})")
      
      self.source_name_changed |= local
      
  def canvas_configure(self, event : tk.Event = None) -> None:
    self.scale = self.screen.scale
    self.redraw()
      
  def redraw(self) -> None:
    self.calculate_canvas_pos()
    gpx = self.get_grabberradius()
    lw = self.get_linewidth()
    
    self.canvas.coords(self.rect_id, self.polygon.to_array())
    self.canvas.itemconfigure(self.rect_id, width = lw)
      
    if self.interactable:
      for id in self.grabber_ids:
        self.canvas.itemconfigure(id, width = lw)
      
      for i in range(0, self.polygon.size()):
        self.canvas.coords(self.grabber_ids[i], self.polygon.point(i).x - gpx, self.polygon.point(i).y - gpx, self.polygon.point(i).x + gpx, self.polygon.point(i).y + gpx)
        
      top_middle = (self.polygon.point(0) + self.polygon.point(1)) / 2.0
      rpx = self.get_rotatordist()
      
      inter_pos = Coords(0, math.copysign(rpx, self.hpx))
      inter_pos.rotate(self.rotation)
      self.rotator_grabber_pos = top_middle - inter_pos
      
      self.canvas.coords(self.rotator_grabber_id, self.rotator_grabber_pos.x - gpx, self.rotator_grabber_pos.y - gpx, self.rotator_grabber_pos.x + gpx, self.rotator_grabber_pos.y + gpx)
      self.canvas.coords(self.rotator_line_id, top_middle.x, top_middle.y, self.rotator_grabber_pos.x, self.rotator_grabber_pos.y)
      
      self.canvas.itemconfigure(self.rotator_line_id, width = lw)
      
    self.canvas.coords(self.item_label_id, self.polygon.point(0).x, self.polygon.point(0).y - lw)
    
    textangle = (-180.0 * self.rotation / math.pi)
    
    self.canvas.itemconfig(self.item_label_id, angle = textangle)
    
  def contains(self, coords : Coords) -> bool:
    return point_in_polygon(self.polygon, coords)
  
  def move_or_resize(self, coords : Coords, zone : int = 10) -> int:
    if not self.interactable:
      return ModifyType.NONE
    
    xs = [p.x for p in self.polygon.points()]
    ys = [p.y for p in self.polygon.points()]
    
    xs.append(self.rotator_grabber_pos.x)
    ys.append(self.rotator_grabber_pos.y)
    
    minx = min(xs)
    maxx = max(xs)
    miny = min(ys)
    maxy = max(ys)
    
    if coords.x < minx - zone \
      or coords.x > maxx + zone \
      or coords.y < miny - zone \
      or coords.y > maxy + zone:
        return ModifyType.NONE
    
    leftside   = distance_from_segment(self.polygon.point(0), self.polygon.point(3), coords) < zone
    rightside  = distance_from_segment(self.polygon.point(1), self.polygon.point(2), coords) < zone
    topside    = distance_from_segment(self.polygon.point(0), self.polygon.point(1), coords) < zone
    bottomside = distance_from_segment(self.polygon.point(2), self.polygon.point(3), coords) < zone
    
    ret = ModifyType.NONE
    if leftside:
      ret |= ModifyType.LEFT
    if rightside:
      ret |= ModifyType.RIGHT
    if topside:
      ret |= ModifyType.TOP
    if bottomside:
      ret |= ModifyType.BOTTOM
    if ret == 0:
      if point_in_polygon(self.polygon, coords):
        ret = ModifyType.MOVE
      elif distance(self.rotator_grabber_pos, coords) < zone:
        ret = ModifyType.ROTATE
      
    return ret
      
  def move_id_to_front(self, id : int, under : int) -> int:
    if id:
      if under:
        self.canvas.tag_raise(id, under)
      else:
        self.canvas.tag_raise(id)
      return id
    return under
  
  def move_to_front(self, under : int = None) -> None:
    last_id = self.move_id_to_front(self.rect_id, under)
    last_id = self.move_id_to_front(self.rotator_grabber_id, last_id)
    last_id = self.move_id_to_front(self.rotator_line_id, last_id)
    if self.grabber_ids:
      for id in self.grabber_ids:
        last_id = self.move_id_to_front(id, last_id)
    last_id = self.move_id_to_front(self.item_label_id, last_id)
      
  def move_id_to_back(self, id : int, above : int) -> int:
    if id:
      if above:
        self.canvas.tag_lower(id, above)
      else:
        self.canvas.tag_lower(id)
      return id
    return above
      
  def move_to_back(self, above : int = None) -> None:
    last_id = self.move_id_to_back(self.rect_id, above)
    last_id = self.move_id_to_back(self.rotator_grabber_id, last_id)
    last_id = self.move_id_to_back(self.rotator_line_id, last_id)
    if self.grabber_ids:
      for id in self.grabber_ids:
        last_id = self.move_id_to_back(id, last_id)
    last_id = self.move_id_to_back(self.item_label_id, last_id)
    
  def setup_color_picker(self, gui : 'Default_GUI', frame : tk.Frame, label : str, callback : Callable[[str], None], row : int = 0) -> int:
    modify_color_label = ttk.Label(frame, text = label)
    modify_color_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    modify_color_frame = ttk.Frame(frame, padding = "2 0 2 10")
    modify_color_frame.grid(column = 0, row = row, rowspan = 2, sticky = (tk.N, tk.W, tk.E, tk.S))
    modify_color_frame.columnconfigure(0, weight = 1)
    modify_color_frame.columnconfigure(1, weight = 1)
    modify_color_frame.columnconfigure(2, weight = 1)
    modify_color_frame.columnconfigure(3, weight = 1)
    modify_color_frame.columnconfigure(4, weight = 1)
    row += 2
    
    set_white  = tk.Button(modify_color_frame, command = lambda: callback("#ffffff"), bg = "#ffffff")
    set_white.grid(column = 0, row = 0, sticky = (tk.W, tk.E))
    set_black  = tk.Button(modify_color_frame, command = lambda: callback("#000000"), bg = "#000000")
    set_black.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    set_red    = tk.Button(modify_color_frame, command = lambda: callback("#ff0000"), bg = "#ff0000")
    set_red.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    set_green  = tk.Button(modify_color_frame, command = lambda: callback("#00ff00"), bg = "#00ff00")
    set_green.grid(column = 1, row = 1, sticky = (tk.W, tk.E))
    set_blue   = tk.Button(modify_color_frame, command = lambda: callback("#0000ff"), bg = "#0000ff")
    set_blue.grid(column = 2, row = 0, sticky = (tk.W, tk.E))
    set_purple = tk.Button(modify_color_frame, command = lambda: callback("#ff00ff"), bg = "#ff00ff")
    set_purple.grid(column = 2, row = 1, sticky = (tk.W, tk.E))
    set_yellow = tk.Button(modify_color_frame, command = lambda: callback("#ffff00"), bg = "#ffff00")
    set_yellow.grid(column = 3, row = 0, sticky = (tk.W, tk.E))
    set_cyan   = tk.Button(modify_color_frame, command = lambda: callback("#00ffff"), bg = "#00ffff")
    set_cyan.grid(column = 3, row = 1, sticky = (tk.W, tk.E))
    set_yellow = tk.Button(modify_color_frame, command = lambda: callback("#999999"), bg = "#999999")
    set_yellow.grid(column = 4, row = 0, sticky = (tk.W, tk.E))
    set_cyan   = tk.Button(modify_color_frame, command = lambda: callback("#55007f"), bg = "#55007f")
    set_cyan.grid(column = 4, row = 1, sticky = (tk.W, tk.E))
    
    return row
      
  def setup_modify_name(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.modify_name_label = ttk.Label(frame, text = "Name:")
    self.modify_name_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    
    self.modify_name_entry = ttk.Entry(frame, textvariable=self.name_strvar)
    self.modify_name_entry.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_update_button(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.update_button = ttk.Button(frame, text = "Update", command = lambda: self.setup_update_dialog(gui))
    self.update_button.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
  
  def setup_standard_buttons(self, gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    self.dupimage = ttk.Button(frame, text = "Duplicate", command = lambda: self.setup_duplicate_dialog(gui))
    self.dupimage.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.deleteimage = ttk.Button(frame, text = "Delete", command = lambda: self.setup_delete_dialog(gui))
    self.deleteimage.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    self.deleteimage = ttk.Button(frame, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = row, sticky = (tk.W, tk.E), pady = (0, 5))
    row += 1
    
    return row
      
  def setup_modify_ui(self, gui : 'Default_GUI') -> None:
    gui.modifyframe.columnconfigure(0, weight = 1)
    
  def queue_move_to_front(self, gui : 'Default_GUI'):
    index_req = simpleobsws.Request('SetSceneItemIndex', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id, 'sceneItemIndex': gui.get_current_scene_items()[0].scene_item_index})
    gui.connection.queue_request(index_req)
    
  def queue_duplicate_req(self, gui : 'Default_GUI'):
    img_req = simpleobsws.Request('DuplicateSceneItem', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id})
    gui.connection.queue_request(img_req)
    
  def setup_duplicate_dialog(self, gui : 'Default_GUI') -> None:
    self.dup_image_dialog = tk.Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.dup_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.dup_image_dialog.protocol("WM_DELETE_WINDOW", self.dup_image_dialog.destroy)
    
    self.dup_image_frame = ttk.Frame(self.dup_image_dialog, padding = "12 12 12 12")
    self.dup_image_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.dup_image_frame.grid_columnconfigure(0, weight = 1)
    
    self.dup_image_name_label = ttk.Label(self.dup_image_frame, text = f"Duplicate \"{self.source_name} ({self.scene_item_id})\"?")
    self.dup_image_name_label.grid(column = 0, columnspan = 2, row = 0, sticky = (tk.W, tk.E))
    
    def dup():
      self.queue_duplicate_req(gui)
      self.dup_image_dialog.destroy()
      
    self.dup_image_submit = ttk.Button(self.dup_image_frame, text = "Yes", command = dup)
    self.dup_image_submit.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
  
    self.dup_image_cancel = ttk.Button(self.dup_image_frame, text = "No", command = self.dup_image_dialog.destroy)
    self.dup_image_cancel.grid(column = 1, row = 1, sticky = (tk.W, tk.E))
    
  def queue_delete_req(self, gui : 'Default_GUI') -> None:
    del_req = simpleobsws.Request('RemoveSceneItem', { 'sceneName': gui.current_scene, 'sceneItemId': self.scene_item_id })
    gui.connection.queue_request(del_req)
    
  def setup_delete_dialog(self, gui : 'Default_GUI') -> None:
    self.del_image_dialog = tk.Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.del_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.del_image_dialog.protocol("WM_DELETE_WINDOW", self.del_image_dialog.destroy)
    
    self.del_image_frame = ttk.Frame(self.del_image_dialog, padding = "12 12 12 12")
    self.del_image_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S))
    self.del_image_frame.grid_columnconfigure(0, weight = 1)
    
    self.del_image_prompt = ttk.Label(self.del_image_frame, text = f"Are you sure you want to delete \"{self.source_name} ({self.scene_item_id})\"?")
    self.del_image_prompt.grid(column = 0, columnspan = 2, row = 0, sticky = (tk.W, tk.E))
    
    def delimg():
      self.queue_delete_req(gui)
      self.del_image_dialog.destroy()
    
    self.del_image_submit = ttk.Button(self.del_image_frame, text = "Yes", command = delimg)
    self.del_image_submit.grid(column = 0, row = 1, sticky = tk.E)
    self.del_image_cancel = ttk.Button(self.del_image_frame, text = "No", command = self.del_image_dialog.destroy)
    self.del_image_cancel.grid(column = 1, row = 1, sticky = tk.E)
    
  def queue_set_input_name(self, gui : 'Default_GUI') -> None:
    namereq = simpleobsws.Request('SetInputName', { 'inputName': self.last_source_name, 'newInputName': self.source_name})
    gui.connection.queue_request(namereq)
    
  def update_info(self) -> None:
    newname = self.name_strvar.get()
      
    if newname != self.source_name:
      self.set_source_name(newname, True)
    
  def setup_update_dialog(self, gui : 'Default_GUI') -> None:
    self.update_input_dialog = tk.Toplevel(gui.root)
    x = gui.root.winfo_x()
    y = gui.root.winfo_y()
    self.update_input_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.update_input_dialog.protocol("WM_DELETE_WINDOW", self.update_input_dialog.destroy)
    
    self.update_input_frame = ttk.Frame(self.update_input_dialog, padding = "12 12 12 12")
    self.update_input_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E, tk.S))
    
    self.update_input_name_label = ttk.Label(self.update_input_frame, text = f"Update name and settings for \"{self.source_name} ({self.scene_item_id})\"?")
    self.update_input_name_label.grid(column = 0, columnspan = 2, row = 0, sticky = (tk.W, tk.E))
    self.update_input_warn_label = ttk.Label(self.update_input_frame, text = f"(this will affect all inputs with the same name)")
    self.update_input_warn_label.grid(column = 0, columnspan = 2, row = 1, sticky = (tk.W, tk.E))
    
    def updatefunc():
      self.update_info()
      self.update_input_dialog.destroy()
      
    self.update_input_submit = ttk.Button(self.update_input_frame, text = "Yes", command = updatefunc)
    self.update_input_submit.grid(column = 0, row = 2, sticky = (tk.W, tk.E))
  
    self.update_input_cancel = ttk.Button(self.update_input_frame, text = "No", command = self.update_input_dialog.destroy)
    self.update_input_cancel.grid(column = 1, row = 2, sticky = (tk.W, tk.E))
    
  def to_dict(self) -> dict:
    return {
      "type": "obs_object",
      "x": self.x,
      "y": self.y,
      "width": self.width,
      "height": self.height,
      "rotation": self.rotation,
      "source_width": self.source_width,
      "source_height": self.source_height,
      "source_name": self.source_name,
      "scene_item_id": self.scene_item_id,
      "scene_item_index": self.scene_item_index,
      "bounds_type": self.bounds_type,
      "interactable": self.interactable
    }
    
  @staticmethod
  def setup_add_input_name(gui : 'Default_GUI', frame : tk.Frame, row : int = 0) -> int:
    gui.new_input_name_label = ttk.Label(frame, text = "Input name", style = "Large.TLabel")
    gui.new_input_name_label.grid(column = 0, row = row, sticky = tk.W)
    row += 1
    gui.new_input_name_entry = ttk.Entry(frame, textvariable = gui.new_input_name_strvar, width = 48, **gui.largefontopt)
    gui.new_input_name_entry.grid(column = 0, row = row, sticky = tk.W, pady = (0, 10))
    row += 1
    
    return row
  
  @staticmethod
  def setup_add_input_buttons(gui : 'Default_GUI', frame : tk.Frame, addcb : Callable, row : int = 0) -> int:
    gui.add_input_button_frame = ttk.Frame(frame)
    gui.add_input_button_frame.grid(column = 0, row = row, sticky= tk.E)
    row += 1
    
    def addinput() -> None:
      addcb()
      gui.close_add_input_dialog()
    
    gui.new_input_submit = ttk.Button(gui.add_input_button_frame, text = "Add", command = addinput, padding = "5 0 0 0", style = "Large.TButton")
    gui.new_input_submit.grid(column = 0, row = 0, sticky = tk.E, padx = (5, 5))
    
    gui.new_input_cancel = ttk.Button(gui.add_input_button_frame, text = "Cancel", command = gui.close_add_input_dialog, style="Large.TButton")
    gui.new_input_cancel.grid(column = 1, row = 0, sticky = tk.E, padx = (5, 5))
    
    return row
  
  @staticmethod
  def setup_create_ui(gui : 'Default_GUI', frame : tk.Frame) -> None:
    row = 0
    row = OBS_Object.setup_add_input_name(frame, row)
  
  @staticmethod
  def queue_add_input_request(gui : 'Default_GUI') -> None:
    None
  
  @staticmethod
  def from_dict(d : dict, canvas : tk.Canvas, screen : 'OBS_Object') -> 'OBS_Object':
    return OBS_Object(d['scene_item_id'], d['scene_item_index'], canvas, screen, d['x'], d['y'], d['width'], d['height'], d['rotation'], d['source_width'], d['source_height'], d['bounds_type'], d['source_name'], d['interactable'])

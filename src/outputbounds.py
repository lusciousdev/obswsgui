import tkinter as tk

import geometryutil as geom
import obs_object as obsobj

class OutputBounds(obsobj.OBS_Object):
  anchor : str = 'center'
  
  def __init__(self, canvas : tk.Canvas, anchor, width : float, height : float, label : str = ""):
    self.canvas = canvas
    self.screen = None
    self.anchor = anchor
    self.x = 0
    self.y = 0
    self.scale = 1.0
    self.width = width
    self.height = height
    self.source_name = label
    
    self.polygon = geom.Polygon([0, 0], [0, 0], [0, 0], [0, 0])
    
    self.rect_id = self.canvas.create_polygon(self.polygon.to_array(), width = self.line_width, outline = self.default_color, fill = '')
    self.item_label_id = self.canvas.create_text(0, 0, anchor = tk.SW, text = self.source_name, fill = self.default_color)
    
  def canvas_configure(self, event : tk.Event = None) -> None:
    self.scale = 1.0 / max(self.height / (self.canvas.winfo_height() * 2.0 / 3.0), self.width / (self.canvas.winfo_width() * 2.0 / 3.0))
    self.redraw()
    
  def redraw(self) -> None:
    lw = self.get_linewidth()
    
    self.polygon.set_point(0, geom.Coords(0, 0))
    self.wpx = self.width  * self.scale
    self.hpx = self.height * self.scale
    
    if (self.anchor == 'center'):
      self.polygon.set_point(0, geom.Coords((self.canvas.winfo_width() - self.wpx) / 2, (self.canvas.winfo_height() - self.hpx) / 2))
      
      self.polygon.set_point(1, geom.Coords(self.polygon.point(0).x + self.wpx, self.polygon.point(0).y))
      self.polygon.set_point(2, geom.Coords(self.polygon.point(0).x + self.wpx, self.polygon.point(0).y + self.hpx))
      self.polygon.set_point(3, geom.Coords(self.polygon.point(0).x,            self.polygon.point(0).y + self.hpx))
    
    self.canvas.coords(self.rect_id, self.polygon.to_array())
    self.canvas.itemconfigure(self.rect_id, width = lw)
      
    self.canvas.coords(self.item_label_id, self.polygon.point(0).x, self.polygon.point(0).y - 1)
    self.canvas.itemconfigure(self.item_label_id, anchor = tk.SW, text = self.source_name)
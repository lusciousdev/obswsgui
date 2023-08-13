from obs_object import *
from tkinter import font

class TextInput(OBS_Object):
  text = ""
  text_id = None
  
  text_font = None
  
  vertical = False
  color = "#fff"
  
  def __init__(self, scene_item_id : int, scene_item_index : int, canvas : Canvas, screen, x : float, y : float, width : float, height : float, source_width : float, source_height : float, bounds_type : str, label : str = "", interactable : bool = True):
    self.text_font = font.Font(family="Helvetica", size = 1)
    
    super().__init__(scene_item_id, scene_item_index, canvas, screen, x, y, width, height, source_width, source_height, bounds_type, label, interactable)
    
    
    self.text_id = self.canvas.create_text((self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0, fill = self.default_color, text = self.text, font = self.text_font, anchor = CENTER)
    
  def remove_from_canvas(self):
    if self.text_id:
      self.canvas.delete(self.text_id)
    return super().remove_from_canvas()
  
  def get_font_size(self):
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
    
  def set_text(self, text):
    if self.text != text:
      self.text = text
      self.canvas.itemconfigure(self.text_id, text = self.text)
      
  def set_vertical(self, vertical):
    if self.vertical != vertical:
      self.vertical = vertical
      self.canvas.itemconfigure(self.text_id, angle = 0 if not self.vertical else 270, anchor = CENTER)
      
  def move_to_front(self, under = None):
    if self.text_id:
      if under:
        self.canvas.tag_raise(self.text_id, under)
      else:
        self.canvas.tag_raise(self.text_id)
        
    return super().move_to_front(self.text_id)
      
  def redraw(self):
    super().redraw()
    
    self.get_font_size()
    
    if self.text_id:
      self.canvas.coords(self.text_id, (self.polygon.point(0).x + self.polygon.point(2).x) / 2.0, (self.polygon.point(0).y + self.polygon.point(2).y) / 2.0)
      self.canvas.itemconfig(self.text_id, font = self.text_font)
      
  def queue_update_req(self, gui):
    newtext = self.modify_text_strvar.get()
    
    if self.text != newtext:
      req = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'text': newtext }})
      gui.requests_queue.append(req)
    
    return super().queue_update_req(gui)
  
  def adjust_modify_ui(self, gui, val):
    if (val.isnumeric()):
      self.counterframe.grid()
    else:
      self.counterframe.grid_remove()
    return True
  
  def setup_modify_ui(self, gui):
    gui.modifyframe.columnconfigure(0, weight = 1)
    
    self.modify_name_label = ttk.Label(gui.modifyframe, text = "Name:")
    self.modify_name_label.grid(column = 0, row = 0, sticky = W)
    
    self.modify_name_strvar = StringVar(gui.root, self.source_name)
    self.modify_name_entry = ttk.Entry(gui.modifyframe, textvariable=self.modify_name_strvar)
    self.modify_name_entry.grid(column = 0, row = 1, sticky = (W, E), pady = (0, 5))
    
    self.modify_text_label = ttk.Label(gui.modifyframe, text = "Text:")
    self.modify_text_label.grid(column = 0, row = 2, sticky = W)
    
    self.modify_text_strvar = StringVar(gui.root, self.text)
    
    self.modify_text_entry = ttk.Entry(gui.modifyframe, textvariable = self.modify_text_strvar, validate = 'all', validatecommand=(gui.modifyframe.register(lambda val: self.adjust_modify_ui(gui, val)), '%P'))
    self.modify_text_entry.grid(column = 0, row = 3, sticky = (W, E), pady = (0, 5))
    
    self.counterframe = ttk.Frame(gui.modifyframe, padding = "0 0 0 10")
    self.counterframe.grid(column = 0, row = 4, sticky = (W, E))
    self.counterframe.columnconfigure(0, weight = 1, uniform = "counterbuttons")
    self.counterframe.columnconfigure(1, weight = 1, uniform = "counterbuttons")
    def dec():
      val = int(self.modify_text_strvar.get()) - 1
      self.modify_text_strvar.set(f"{val}")
      self.queue_update_req(gui)
    self.decrement = ttk.Button(self.counterframe, text = "--", command = dec, width = 10)
    self.decrement.grid(column = 0, row = 0, padx = (2, 2), sticky = (W, E))
    def inc():
      val = int(self.modify_text_strvar.get()) + 1
      self.modify_text_strvar.set(f"{val}")
      self.queue_update_req(gui)
    self.increment = ttk.Button(self.counterframe, text = "++", command = inc)
    self.increment.grid(column = 1, row = 0, padx = (2, 2), sticky = (W, E))
    
    self.update_button = ttk.Button(gui.modifyframe, text = "Update", command = lambda: self.setup_update_dialog(gui))
    self.update_button.grid(column = 0, row = 5, sticky = (W, E), pady = (0, 5))
    
    self.dupimage = ttk.Button(gui.modifyframe, text = "Duplicate", command = lambda: self.setup_duplicate_dialog(gui))
    self.dupimage.grid(column = 0, row = 6, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Delete", command = lambda: self.setup_delete_dialog(gui))
    self.deleteimage.grid(column = 0, row = 7, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = 8, sticky = (W, E), pady = (0, 5))
    
    self.adjust_modify_ui(gui, self.modify_text_strvar.get())
    
    return super().setup_modify_ui(gui)
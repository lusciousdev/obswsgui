from obs_object import *
from PIL import Image, ImageTk
import requests

class ImageInput(OBS_Object):
  img_url = ""
  img_id = None
  orig_img = None
  resized_img = None
  transformed_img = None
  tk_img = None
  
  def remove_from_canvas(self):
    super().remove_from_canvas()
    if self.img_id:
      self.canvas.delete(self.img_id)
  
  def redraw(self):
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
        self.img_id = self.canvas.create_image(imgx, imgy, image = self.tk_img, anchor = NW)
      else:
        self.canvas.coords(self.img_id, imgx, imgy)
        self.canvas.itemconfigure(self.img_id, image = self.tk_img)
    
  def set_image_url(self, url : str):
    if self.img_url != url:
      try:
        self.img_url = url
        self.orig_img = Image.open(requests.get(self.img_url, stream = True).raw)
        print(f"image loaded from {url}")
      except:
        print(f"failed to load image from {url}")
        self.orig_img = None
      self.redraw()
      
  def move_to_front(self, under = None):
    if self.img_id:
      if under:
        self.canvas.tag_raise(self.img_id, under)
      else:
        self.canvas.tag_raise(self.img_id)
        
    return super().move_to_front(self.img_id)
    
  def queue_update_req(self, gui):
    newname = self.modify_name_strvar.get()
    newurl = self.modify_url_strvar.get()
    
    if newurl != self.img_url:
      urlreq = simpleobsws.Request('SetInputSettings', { 'inputName': self.source_name, 'inputSettings': { 'file': self.modify_url_entry.get() }})
      gui.requests_queue.append(urlreq)
    if newname != self.source_name:
      namereq = simpleobsws.Request('SetInputName', { 'inputName': self.source_name, 'newInputName': self.modify_name_strvar.get()})
      gui.requests_queue.append(namereq)
  
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
    
    self.update_button = ttk.Button(gui.modifyframe, text = "Update", command = lambda: self.setup_update_dialog(gui))
    self.update_button.grid(column = 0, row = 4, sticky = (W, E), pady = (0, 5))
    
    self.dupimage = ttk.Button(gui.modifyframe, text = "Duplicate", command = lambda: self.setup_duplicate_dialog(gui))
    self.dupimage.grid(column = 0, row = 5, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Delete", command = lambda: self.setup_delete_dialog(gui))
    self.deleteimage.grid(column = 0, row = 6, sticky = (W, E), pady = (0, 5))
    
    self.deleteimage = ttk.Button(gui.modifyframe, text = "Move to front", command = lambda: self.queue_move_to_front(gui))
    self.deleteimage.grid(column = 0, row = 7, sticky = (W, E), pady = (0, 5))
    
    return super().setup_modify_ui(gui)
  
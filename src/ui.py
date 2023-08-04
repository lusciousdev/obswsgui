import logging
logging.basicConfig(level = logging.INFO)

import asyncio
import time

from tkinter import *
from tkinter import ttk

import simpleobsws

from obs_object import *

class OBS_WS_GUI:
  ready_to_connect = False
  connected = False
  ws = None
  requests_queue = []
  
  video_width = 1920
  video_height = 1080
  
  canvas = None
  screen = None
  current_scene = ""
  scene_items = []
  selected_item = None
  
  lastpos = Coords()
  
  manip_mode = None
  
  def __init__(self, root : Tk):
    self.root = root
    
    self.root.title("OBS WebSocket GUI")
    self.root.geometry("480x320")
    
    self.root.columnconfigure(0, weight = 1)
    self.root.rowconfigure(0, weight = 1)
    
    self.ip_addr_strvar = StringVar(self.root, value = "127.0.0.1")
    self.port_strvar = StringVar(self.root, "4455")
    self.pw_strvar = StringVar(self.root, "testpw")
    self.conn_submit_strvar = StringVar(self.root, "Connect")
    
    self.new_image_name_strvar = StringVar(self.root, "")
    self.new_image_url_strvar = StringVar(self.root, "")
    
    self.dup_image_name_strvar = StringVar(self.root, "")
    
    self.setup_connection_ui()
    
  def clear_root(self):
    for ele in self.root.winfo_children():
      ele.destroy()
    
  def setup_connection_ui(self):
    options = { 'font': (None, 16) }
    
    s = ttk.Style()
    s.configure("Conn.TButton", font = options['font'])
    
    self.connframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.connframe.place(relx = 0.5, rely = 0.5, anchor = CENTER)
    
    self.ip_addr_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.ip_addr_frame.grid(column = 0, row = 0, sticky = (N, W, E))
    
    self.ip_addr_label = ttk.Label(self.ip_addr_frame, text = "IP Address/URL", **options)
    self.ip_addr_label.grid(column = 0, row = 0, sticky = W)
    self.port_label = ttk.Label(self.ip_addr_frame, text = "Port", **options)
    self.port_label.grid(column = 1, row = 0, sticky = W)
    
    self.ip_addr_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.ip_addr_strvar, width = 25, **options)
    self.ip_addr_entry.grid(column = 0, row = 1, sticky = (W, E))
    self.port_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.port_strvar, width = 8, **options)
    self.port_entry.grid(column = 1, row = 1, sticky = (W, E))
    
    self.pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.pw_frame.grid(column = 0, row = 1, sticky = (S, W, E))
    self.pw_frame.grid_columnconfigure(1, weight = 1)
    
    self.pw_label = ttk.Label(self.pw_frame, text = "Password: ", **options)
    self.pw_label.grid(column = 0, row = 0)
    self.pw_entry = ttk.Entry(self.pw_frame, textvariable = self.pw_strvar, **options)
    self.pw_entry.grid(column = 1, row = 0, sticky = (W, E))
    
    self.conn_submit = ttk.Button(self.connframe, textvariable = self.conn_submit_strvar, style="Conn.TButton", command = self.start_connection_attempt)
    self.conn_submit.grid(column = 0, row = 2, sticky = (W, E))
    
  def canvas_to_scene(self, coords : Coords):
    scene_coords = Coords()
    scene_coords.x = round((coords.x - self.screen.xpx) / self.screen.scale)
    scene_coords.y = round((coords.y - self.screen.ypx) / self.screen.scale)
    return scene_coords
  
  def update_lastpos(self, x, y):
    self.lastpos.x = x
    self.lastpos.y = y
    
  def get_items_under_mouse(self, coords : Coords):
    items_under = []
    
    for item in self.scene_items:
      manip_mode = item.move_or_resize(coords)
      if manip_mode:
        items_under.append((item, manip_mode))
        
    return items_under

  def mouseDown(self, event):
    self.update_lastpos(event.x, event.y)
    
    scene_coords = self.canvas_to_scene(self.lastpos)
    
    items_under = self.get_items_under_mouse(scene_coords)
    
    for item in self.scene_items:
      if item.selected:
        in_under = False
        for under_item in items_under:
          if item.scene_item_id == under_item[0].scene_item_id:
            in_under = True
            break
        item.selected = in_under
    
    already_focused = False
    for item in items_under:
      if item[0].selected:
        already_focused = True
        self.manip_mode = item[1]
    if not already_focused and len(items_under) > 0:
      self.manip_mode = items_under[0][1]
      items_under[0][0].selected = True
          
  def doubleClick(self, event):
    self.update_lastpos(event.x, event.y)
    
    scene_coords = self.canvas_to_scene(self.lastpos)
    
    items_under = self.get_items_under_mouse(scene_coords)
    
    for item in self.scene_items:
      if item.selected:
        in_under = False
        for under_item in items_under:
          if item.scene_item_id == under_item[0].scene_item_id:
            in_under = True
            break
        item.selected = in_under
    
    already_focused = False
    for i in range(0, len(items_under)):
      if items_under[i][0].selected:
        already_focused = True
        if len(items_under) > (i + 1):
          items_under[i][0].selected = False
          items_under[i + 1][0].selected = True
          self.manip_mode = items_under[i+1][1]
        if i > 0 and i == len(items_under) - 1:
          items_under[i][0].selected = False
          items_under[0][0].selected = True
          self.manip_mode = items_under[0][1]
        break
    if not already_focused and len(items_under) > 0:
      self.manip_mode = items_under[0][1]
      items_under[0][0].selected = True

  def mouseMove(self, event):
    diffX = round((event.x - self.lastpos.x) / self.screen.scale)
    diffY = round((event.y - self.lastpos.y) / self.screen.scale)
    for item in self.scene_items:
      if item.selected:
        if self.manip_mode == MOVE:
          item.x += diffX
          item.y += diffY
        else:
          if self.manip_mode == LEFT or self.manip_mode == TOPLEFT or self.manip_mode == BOTTOMLEFT:
            item.x += diffX
            item.width -= diffX
          if self.manip_mode == RIGHT or self.manip_mode == TOPRIGHT or self.manip_mode == BOTTOMRIGHT:
            item.width += diffX
          if self.manip_mode == TOP or self.manip_mode == TOPLEFT or self.manip_mode == TOPRIGHT:
            item.y += diffY
            item.height -= diffY
          if self.manip_mode == BOTTOM or self.manip_mode == BOTTOMLEFT or self.manip_mode == BOTTOMRIGHT:
            item.height += diffY
        self.queue_set_item_transform(item)
        
    self.update_lastpos(event.x, event.y)
    
  def mouseUp(self, event):
    # for item in self.scene_items:
    #   item.selected = False
    return
  
  def get_selected_item(self):
    for item in self.scene_items:
      if item.selected:
        return item
    return None
      
  def clear_canvas(self):
    self.canvas.delete("all")
    
  def draw(self, event = None):
    if self.canvas:
      if self.screen:
        self.screen.draw()
      
      for overlay in self.scene_items:
        overlay.draw()
        
  def queue_set_item_transform(self, item : OBS_Object):
    scale_x = 1.0 if item.source_width == 0.0 else item.width / item.source_width
    scale_y = 1.0 if item.source_height == 0.0 else item.height / item.source_height
    if item.bounds_type == 'OBS_BOUNDS_SCALE_INNER':
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': self.current_scene, 'sceneItemId': item.scene_item_id, 'sceneItemTransform': { 'positionX': item.x, 'positionY': item.y, 'boundsWidth': item.width, 'boundsHeight': item.height }})
    else:
      tf_req = simpleobsws.Request('SetSceneItemTransform', { 'sceneName': self.current_scene, 'sceneItemId': item.scene_item_id, 'sceneItemTransform': { 'positionX': item.x, 'positionY': item.y, 'scaleX': scale_x, 'scaleY': scale_y }})
      
    self.requests_queue.append(tf_req)
    
  def setup_default_ui(self):
    self.defaultframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.defaultframe.pack(anchor = CENTER, fill = BOTH, expand = True)
    self.defaultframe.columnconfigure(0, weight = 1)
    self.defaultframe.rowconfigure(0, weight=1)
    
    self.canvas = Canvas(self.defaultframe, width = 480, height = 270, background = "white")
    self.canvas.grid(column = 0, row = 0, sticky = (N, W, E, S))
        
    self.canvas.bind("<Configure>", self.draw)
    self.canvas.bind("<Button-1>", self.mouseDown)
    self.canvas.bind("<Double-Button-1>", self.doubleClick)
    self.canvas.bind("<ButtonRelease-1>", self.mouseUp)
    self.canvas.bind("<B1-Motion>", self.mouseMove)
    
    self.uiframe = ttk.Frame(self.defaultframe, padding = "12 12 12 12")
    self.uiframe.grid(column = 0, row = 1, sticky = (S, W, E))
    
    self.addimage = ttk.Button(self.uiframe, text = "Add", command = self.setup_add_image_dialog)
    self.addimage.grid(column = 0, row = 0, sticky = W)
    
    self.dupimage = ttk.Button(self.uiframe, text = "Duplicate", command = self.setup_duplicate_image_dialog)
    self.dupimage.grid(column = 1, row = 0, sticky = W)
    
    self.deleteimage = ttk.Button(self.uiframe, text = "Delete", command = self.setup_delete_image_dialog)
    self.deleteimage.grid(column = 2, row = 0, sticky = W)
    
    self.deleteimage = ttk.Button(self.uiframe, text = "Move to front", command = self.move_selected_to_front)
    self.deleteimage.grid(column = 3, row = 0, sticky = W)
    
    self.screen = ScreenObj(self.canvas, anchor = CENTER, width = self.video_width, height = self.video_height, label = "Screen")
    
  def setup_add_image_dialog(self):
    self.add_image_dialog = Toplevel(self.root)
    x = self.root.winfo_x()
    y = self.root.winfo_y()
    self.add_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.add_image_dialog.protocol("WM_DELETE_WINDOW", self.close_add_image_dialog)
    
    self.add_image_frame = ttk.Frame(self.add_image_dialog, padding = "12 12 12 12")
    self.add_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.add_image_frame.grid_columnconfigure(0, weight = 1)
    
    self.new_image_name_label = ttk.Label(self.add_image_frame, text = "Image name")
    self.new_image_name_label.grid(column = 0, row = 0, sticky = W)
    self.new_image_name_entry = ttk.Entry(self.add_image_frame, textvariable = self.new_image_name_strvar, width = 48)
    self.new_image_name_entry.grid(column = 0, row = 1, sticky = W)
    
    self.new_image_url_label = ttk.Label(self.add_image_frame, text = "Image URL (must be online)")
    self.new_image_url_label.grid(column = 0, row = 2, sticky = W)
    self.new_image_url_entry = ttk.Entry(self.add_image_frame, textvariable = self.new_image_url_strvar, width = 48)
    self.new_image_url_entry.grid(column = 0, row = 3, sticky = W)
    
    self.add_image_button_frame = ttk.Frame(self.add_image_frame)
    self.add_image_button_frame.grid(column = 0, row = 5, sticky=E)
    
    
    def addimg():
      self.queue_add_image_req()
      self.close_add_image_dialog()
    
    self.new_image_submit = ttk.Button(self.add_image_button_frame, text = "Add image", command = addimg)
    self.new_image_submit.grid(column = 0, row = 0, sticky = E)
  
    self.new_image_cancel = ttk.Button(self.add_image_button_frame, text = "Cancel", command = self.close_add_image_dialog)
    self.new_image_cancel.grid(column = 1, row = 0, sticky = E)
    
  def close_add_image_dialog(self):
    self.new_image_name_strvar.set("")
    self.new_image_url_strvar.set("")
    self.add_image_dialog.destroy()
    
  def setup_duplicate_image_dialog(self):
    self.dup_image_dialog = Toplevel(self.root)
    x = self.root.winfo_x()
    y = self.root.winfo_y()
    self.dup_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.dup_image_dialog.protocol("WM_DELETE_WINDOW", self.close_dup_image_dialog)
    
    self.dup_image_frame = ttk.Frame(self.dup_image_dialog, padding = "12 12 12 12")
    self.dup_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.dup_image_frame.grid_columnconfigure(0, weight = 1)
    
    selected_item = self.get_selected_item()
    
    if selected_item:
      self.dup_image_name_label = ttk.Label(self.dup_image_frame, text = f"Duplicate \"{selected_item.label}\"?")
      self.dup_image_name_label.grid(column = 0, columnspan = 2, row = 0, sticky = (W, E))
      
      def dup():
        self.queue_duplicate_image_req()
        self.close_dup_image_dialog()
        
      self.dup_image_submit = ttk.Button(self.dup_image_frame, text = "Yes", command = dup)
      self.dup_image_submit.grid(column = 0, row = 1, sticky = (W, E))
    
      self.dup_image_cancel = ttk.Button(self.dup_image_frame, text = "No", command = self.close_dup_image_dialog)
      self.dup_image_cancel.grid(column = 1, row = 1, sticky = (W, E))
    else:
      self.dup_image_name_label = ttk.Label(self.dup_image_frame, text = f"No item selected.")
      self.dup_image_name_label.grid(column = 0, row = 0, sticky = (W, E))
    
      self.dup_image_cancel = ttk.Button(self.dup_image_frame, text = "Cancel", command = self.close_dup_image_dialog)
      self.dup_image_cancel.grid(column = 0, row = 1, sticky = (W, E))
      
    
  def close_dup_image_dialog(self):
    self.dup_image_name_strvar.set("")
    self.dup_image_dialog.destroy()
    
  def setup_delete_image_dialog(self):
    self.del_image_dialog = Toplevel(self.root)
    x = self.root.winfo_x()
    y = self.root.winfo_y()
    self.del_image_dialog.geometry(f"+{x + 200}+{y + 200}")
    
    self.del_image_dialog.protocol("WM_DELETE_WINDOW", self.del_image_dialog.destroy)
    
    self.del_image_frame = ttk.Frame(self.del_image_dialog, padding = "12 12 12 12")
    self.del_image_frame.grid(column = 0, row = 0, sticky = (N, W, E, S))
    self.del_image_frame.grid_columnconfigure(0, weight = 1)
    
    selected_item = self.get_selected_item()
    
    if selected_item:
      self.del_image_prompt = ttk.Label(self.del_image_frame, text = f"Are you sure you want to delete \"{selected_item.label}\"?")
      self.del_image_prompt.grid(column = 0, columnspan = 2, row = 0, sticky = (W, E))
      
      def delimg():
        self.queue_delete_image_req()
        self.del_image_dialog.destroy()
      
      self.del_image_submit = ttk.Button(self.del_image_frame, text = "Yes", command = delimg)
      self.del_image_submit.grid(column = 0, row = 1, sticky = E)
      self.del_image_cancel = ttk.Button(self.del_image_frame, text = "No", command = self.del_image_dialog.destroy)
      self.del_image_cancel.grid(column = 1, row = 1, sticky = E)
    else:
      self.del_image_prompt = ttk.Label(self.del_image_frame, text = f"No item selected.")
      self.del_image_prompt.grid(column = 0, row = 0, sticky = (W, E))
      self.del_image_cancel = ttk.Button(self.del_image_frame, text = "Cancel", command = self.del_image_dialog.destroy)
      self.del_image_cancel.grid(column = 0, row = 1, sticky = (W, E))
    
  def queue_add_image_req(self):
    img_name = self.new_image_name_strvar.get()
    img_url  = self.new_image_url_strvar.get()
    
    if img_name != "" and img_url != "":
      img_req  = simpleobsws.Request('CreateInput', { 'sceneName': self.current_scene, 'inputName': img_name, 'inputKind': 'image_source', 'inputSettings': { 'file': img_url }, 'sceneItemEnabled': True })
      self.requests_queue.append(img_req)
    
  def queue_duplicate_image_req(self):
    selected_item = self.get_selected_item()
    img_req = simpleobsws.Request('DuplicateSceneItem', { 'sceneName': self.current_scene, 'sceneItemId': selected_item.scene_item_id})
    self.requests_queue.append(img_req)
    
  def queue_delete_image_req(self):
    selected_item = None
    for item in self.scene_items:
      if item.selected:
        selected_item = item
        
    del_req = simpleobsws.Request('RemoveSceneItem', { 'sceneName': self.current_scene, 'sceneItemId': selected_item.scene_item_id })
    self.requests_queue.append(del_req)
    
  def move_selected_to_front(self):
    selected_item = self.get_selected_item()
    if selected_item:
      selected_item.move_to_front()
      index_req = simpleobsws.Request('SetSceneItemIndex', { 'sceneName': self.current_scene, 'sceneItemId': selected_item.scene_item_id, 'sceneItemIndex': self.scene_items[0].scene_item_index})
      self.requests_queue.append(index_req)
  
  def set_conn_ui_state(self, disabled : bool, submit_str : str):
    self.conn_submit_strvar.set(submit_str)
    state = 'disable' if disabled else 'enable'
    self.ip_addr_entry['state'] = state
    self.port_entry['state'] = state
    self.pw_entry['state'] = state
    self.conn_submit['state'] = state
    
  def start_connection_attempt(self):
    self.set_conn_ui_state(True, "Attempting connection...")
    self.ready_to_connect = True
    
  def start_async_loop(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
      self.draw()
      loop.run_until_complete(self.async_update())
      time.sleep(1.0 / 25.0)
    
  async def async_update(self):
    if not self.connected and self.ready_to_connect:
      success = await self.attempt_connection()
      if success:
        self.set_conn_ui_state(True, "Connected.")
        self.clear_root()
        self.setup_default_ui()
      else:
        self.set_conn_ui_state(False, "Failed to connect. Retry?")
    if self.connected:      
      await self.send_requests()
      await self.get_scene_state()
    
  async def attempt_connection(self):
    self.ready_to_connect = False
      
    ip_addr = self.ip_addr_strvar.get()
    port = self.port_strvar.get()
    password = self.pw_strvar.get()
    
    self.conn_submit_strvar.set("Attempting to connect...")
    
    self.ws = simpleobsws.WebSocketClient(url = f"ws://{ip_addr}:{port}", password = password)
    
    connected = await self.ws.connect()
    identified = await self.ws.wait_until_identified()
    
    if connected and identified:
      self.connected = True
      logging.info("Connected and identified.")
    else:
      self.connected = False
      logging.error("Failed to connect or identify.")
      return False
    
    req = simpleobsws.Request('GetVideoSettings')
    ret = await self.ws.call(req)
    
    if not ret.ok():
      logging.error("Failed to fetch scene item ID!")
      self.connected = False
      return False
  
    self.video_width = ret.responseData["baseWidth"]
    self.video_height = ret.responseData["baseHeight"]
    
    return True
  
  def find_scene_item(self, item_id):
    for item in self.scene_items:
      if (item.scene_item_id == item_id):
        return item
    return None
  
  async def get_scene_state(self):
    req = simpleobsws.Request('GetCurrentProgramScene')
    ret = await self.ws.call(req)
    
    if not ret.ok():
      logging.error("Failed to get current scene.")
      return False
    
    active_scene = ret.responseData["currentProgramSceneName"]
    if self.current_scene != active_scene:
      self.current_scene = active_scene
      self.scene_items.clear()
    
    req = simpleobsws.Request('GetSceneItemList', { 'sceneName' : self.current_scene })
    ret = await self.ws.call(req)
    
    if not ret.ok():
      logging.error("Failed to get scene items")
    
    item_list = ret.responseData['sceneItems']
    
    for saved in self.scene_items:
      found = False
      for active in item_list:
        if saved.scene_item_id == active['sceneItemId']:
          found = True
          break
      if not found:
        self.scene_items.remove(saved)
        del saved
        
    for i in item_list:
      item = self.find_scene_item(i['sceneItemId'])
      tf = i['sceneItemTransform']
      
      # print(i)
      # print(f"X: {tf['positionX']} Y: {tf['positionY']} W: {tf['width']} H: {tf['height']} BW: {tf['boundsWidth']} BH: {tf['boundsHeight']} SX: {tf['scaleX']} SY: {tf['scaleY']} CL: {tf['cropLeft']} CR: {tf['cropRight']}")
      
      x = tf['positionX']
      y = tf['positionY']
      
      w = tf['width']
      h = tf['height']
      
      sw = tf['sourceWidth']
      sh = tf['sourceHeight']
      
      if tf['boundsType'] == 'OBS_BOUNDS_SCALE_INNER':
        w = tf['boundsWidth']
        h = tf['boundsHeight']
      
      if item:
        item.x = x
        item.y = y
        item.width = w
        item.height = h
        item.label = i['sourceName']
        item.scene_item_index = i['sceneItemIndex']
      else:
        item = OBS_Object(i['sceneItemId'], i['sceneItemIndex'], self.canvas, self.screen, x, y, w, h, sw, sh, tf['boundsType'], i['sourceName'])
        
        if i['inputKind'] == 'image_source':
          req = simpleobsws.Request('GetInputSettings', { 'inputName': i['sourceName'] })
          ret = await self.ws.call(req)
          
          if not ret.ok():
            self.log_request_error(ret)
          else:
            url = ret.responseData['inputSettings']['file']
            item.set_image(url)
        else:
          item.interactable = False
          
        self.scene_items.append(item)
            
    # sort the scene items to match the OBS source list
    self.scene_items.sort(key = lambda item: item.scene_item_index, reverse = True)
    
    for i in range(1, len(self.scene_items)):
      self.scene_items[i - 1].move_to_front(self.scene_items[i])
    
  async def send_requests(self):
    for req in self.requests_queue:
      ret = await self.ws.call(req)
      
      if not ret.ok():
        self.log_request_error(ret)
        
    self.requests_queue.clear()
    
  def log_request_error(self, ret):
    logging.error(f"Error {ret.requestStatus['code']}: {ret.requestStatus['comment']}")
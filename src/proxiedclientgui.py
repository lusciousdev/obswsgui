import logging

logging.basicConfig(level = logging.INFO)

import threading
import tkinter as tk
from tkinter import font, ttk

import simpleobsws

import obswsgui as owg
import proxiedclientconn as pcc


class ProxiedOBS_WS_GUI(owg.OBS_WS_GUI):
  connection : pcc.ProxiedClientConnection = None
  
  framerate = 10.0
    
  async def attempt_connection(self):
    self.ready_to_connect = False
      
    ip_addr = self.ip_addr_strvar.get()
    port = self.port_strvar.get()
    roomcode = self.pw_strvar.get()
    url = f"{ip_addr}:{port}"
    
    self.conn_submit_strvar.set("Attempting to connect...")
    
    self.connection = pcc.ProxiedClientConnection(url = url, roomcode = roomcode, error_handler = self.log_request_error)
    
    self.connected = await self.connection.connect()
    if not self.connected:  
      return False
    
    req = simpleobsws.Request('GetVersion')
    ret = await self.connection.request(req)
    
    if not ret:
      self.connected = False
      return False

    self.platform = ret.responseData['platform']
    
    screenw, screenh = await self.get_video_settings()
    
    if not screenw or not screenh:
      return False
    else:
      self.output_width = screenw
      self.output_height = screenh
      return True
    
  def setup_connection_ui(self) -> None:
    self.connframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.connframe.place(relx = 0.5, rely = 0.5, anchor = tk.CENTER)
    
    self.ip_addr_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.ip_addr_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E))
    
    self.ip_addr_label = ttk.Label(self.ip_addr_frame, text = "IP Address/URL", style="Large.TLabel")
    self.ip_addr_label.grid(column = 0, row = 0, sticky = tk.W)
    self.port_label = ttk.Label(self.ip_addr_frame, text = "Port", style="Large.TLabel")
    self.port_label.grid(column = 1, row = 0, sticky = tk.W)
    
    self.ip_addr_strvar.set("http://127.0.0.1")
    self.ip_addr_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.ip_addr_strvar, width = 25, **self.largefontopt)
    self.ip_addr_entry.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    self.port_strvar.set("5544")
    self.port_entry = ttk.Entry(self.ip_addr_frame, textvariable = self.port_strvar, width = 8, **self.largefontopt)
    self.port_entry.grid(column = 1, row = 1, sticky = (tk.W, tk.E))
    
    self.pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.pw_frame.grid(column = 0, row = 1, sticky = (tk.S, tk.W, tk.E))
    self.pw_frame.grid_columnconfigure(1, weight = 1)
    
    self.pw_label = ttk.Label(self.pw_frame, text = "Room code: ", style="Large.TLabel")
    self.pw_label.grid(column = 0, row = 0)
    
    self.pw_strvar.set("roomcode")
    self.pw_entry = ttk.Entry(self.pw_frame, textvariable = self.pw_strvar, **self.largefontopt)
    self.pw_entry.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    
    self.conn_submit = ttk.Button(self.connframe, textvariable = self.conn_submit_strvar, command = self.start_connection_attempt, style="Large.TButton")
    self.conn_submit.grid(column = 0, row = 2, sticky = (tk.W, tk.E))
    
if __name__ == '__main__':
  root = tk.Tk()
  client = ProxiedOBS_WS_GUI(root)
  
  _thread = threading.Thread(target=client.start_async_loop, daemon=True)
  _thread.start()
  
  root.mainloop()
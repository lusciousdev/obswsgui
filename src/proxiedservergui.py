import logging

logging.basicConfig(level = logging.INFO)

import asyncio
import datetime as dt
import tkinter as tk
from tkinter import ttk, font
import typing
import time
import threading
import uuid

import simpleobsws

import proxiedserverconn as psc

class ProxiedServerClient:
  ready_to_connect : bool = False
  connected : bool = False
  
  connection : psc.ProxiedServerConnection = None
  
  framerate : float = 60.0
  
  defaultfontopt : dict = { 'font': ("Helvetica",  9) }
  largefontopt   : dict = { 'font': ("Helvetica", 16) }
  hugefontopt    : dict = { 'font': ("Helvetica", 24) }
  
  background_color  : str = "#0e0e10"
  background_medium : str = "#18181b"
  background_light  : str = "#1f1f23"
  background_button : str = "#2e2e35"
  text_color        : str = "#efeff1"
  accent_color      : str = "#fab4ff"
  
  style : ttk.Style = None
  
  def __init__(self, root : tk.Tk) -> None:
    self.root = root
    
    self.root.title("Proxied Server GUI")
    self.root.geometry("720x400")
    self.root.minsize(320, 180)
    self.root.configure(background = self.background_color)
    
    self.root.columnconfigure(0, weight = 1)
    self.root.rowconfigure(0, weight = 1)
    
    self.ws_addr_strvar = tk.StringVar(self.root, value = "ws://127.0.0.1:4455")
    self.ws_pw_strvar   = tk.StringVar(self.root, "testpw")
    
    self.proxy_addr_strvar = tk.StringVar(self.root, value = "ws://127.0.0.1:5544")
    self.proxy_code_strvar = tk.StringVar(self.root, str(uuid.uuid4()))
    
    self.conn_submit_strvar = tk.StringVar(self.root, "Connect")
    
    self.style = ttk.Style(self.root)
    self.style.theme_create("proxiedservergui", parent = "alt", settings = {
      ".": {
        "configure": {
          "background": self.background_color,
          "foreground": self.text_color
        }
      },
      "TButton": {
        "configure": {
          "anchor": "center",
          "background": self.background_light,
        },
        "map": {
          "background": [('active', self.background_button)]
        }
      },
      "TEntry": {
        "configure": {
          "background": self.text_color,
          "foreground": self.background_color
        }
      },
      "TMenubutton": {
        "configure": {
          "background": self.background_button,
          "foreground": self.text_color
        }
      },
      "Large.TLabel": {
        "configure": self.largefontopt
      },
      "Large.TButton": {
        "configure": self.largefontopt
      },
      "Large.TMenubutton": {
        "configure": self.largefontopt
      },
      "Huge.TLabel": {
        "configure": self.hugefontopt
      },
      "Huge.TButton": {
        "configure": self.hugefontopt
      }
    })
    self.style.theme_use("proxiedservergui")
    
    self.setup_connection_ui()
    
  def start_async_loop(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
      loop.run_until_complete(self.async_update())
    
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
      await self.connection.update()
      
      if not self.connection.connected:
        self.reset_to_connection_ui()
    
  def clear_root(self) -> None:
    for ele in self.root.winfo_children():
      ele.destroy()
    
  def setup_connection_ui(self) -> None:
    self.connframe = ttk.Frame(self.root, padding = "12 12 12 12")
    self.connframe.place(relx = 0.5, rely = 0.5, anchor = tk.CENTER)
    
    self.websocket_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.websocket_frame.grid(column = 0, row = 0, sticky = (tk.N, tk.W, tk.E))
    self.websocket_frame.columnconfigure(0, weight = 1)
    
    self.ip_addr_label = ttk.Label(self.websocket_frame, text = "OBS WebSocket address", style="Large.TLabel")
    self.ip_addr_label.grid(column = 0, row = 0, sticky = tk.W)
    
    self.ws_ip_addr_entry = ttk.Entry(self.websocket_frame, textvariable = self.ws_addr_strvar, width = 25, **self.largefontopt)
    self.ws_ip_addr_entry.grid(column = 0, row = 1, sticky = (tk.W, tk.E))
    
    self.websocket_pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.websocket_pw_frame.grid(column = 0, row = 1, sticky = (tk.S, tk.W, tk.E))
    self.websocket_pw_frame.grid_columnconfigure(1, weight = 1)
    
    self.ws_pw_label = ttk.Label(self.websocket_pw_frame, text = "Password: ", style="Large.TLabel")
    self.ws_pw_label.grid(column = 0, row = 0)
    self.ws_pw_entry = ttk.Entry(self.websocket_pw_frame, textvariable = self.ws_pw_strvar, **self.largefontopt)
    self.ws_pw_entry.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    
    self.proxy_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.proxy_frame.grid(column = 0, row = 2, sticky = (tk.N, tk.W, tk.E))
    self.proxy_frame.columnconfigure(0, weight = 1)
    
    self.proxy_ip_addr_label = ttk.Label(self.proxy_frame, text = "Proxy server address", style="Large.TLabel")
    self.proxy_ip_addr_label.grid(column = 0, columnspan=2, row = 0, sticky = tk.W)
    
    self.proxy_ip_addr_entry = ttk.Entry(self.proxy_frame, textvariable = self.proxy_addr_strvar, width = 25, **self.largefontopt)
    self.proxy_ip_addr_entry.grid(column = 0, columnspan=2, row = 1, sticky = (tk.W, tk.E))
    
    self.proxy_pw_frame = ttk.Frame(self.connframe, padding = "2 2 2 2")
    self.proxy_pw_frame.grid(column = 0, row = 3, sticky = (tk.S, tk.W, tk.E))
    self.proxy_pw_frame.grid_columnconfigure(1, weight = 1)
    
    self.proxy_pw_label = ttk.Label(self.proxy_pw_frame, text = "Room code: ", style="Large.TLabel")
    self.proxy_pw_label.grid(column = 0, row = 0)
    self.proxy_pw_entry = ttk.Entry(self.proxy_pw_frame, textvariable = self.proxy_code_strvar, **self.largefontopt)
    self.proxy_pw_entry.grid(column = 1, row = 0, sticky = (tk.W, tk.E))
    
    self.conn_submit = ttk.Button(self.connframe, textvariable = self.conn_submit_strvar, command = self.start_connection_attempt, style="Large.TButton")
    self.conn_submit.grid(column = 0, row = 4, sticky = (tk.W, tk.E))
  
  def set_conn_ui_state(self, disabled : bool, submit_str : str) -> None:
    self.conn_submit_strvar.set(submit_str)
    state = 'disable' if disabled else 'enable'
    self.ws_ip_addr_entry['state'] = state
    self.ws_pw_entry['state'] = state
    self.proxy_ip_addr_entry['state'] = state
    self.proxy_pw_entry['state'] = state
    self.conn_submit['state'] = state
      
  def reset_to_connection_ui(self) -> None:
      self.connected = False
      self.ready_to_connect = False
      self.clear_root()
      self.setup_connection_ui()
    
  def start_connection_attempt(self) -> None:
    self.set_conn_ui_state(True, "Attempting connection...")
    self.ready_to_connect = True
    
  async def attempt_connection(self):
    self.ready_to_connect = False
      
    ws_addr = self.ws_addr_strvar.get()
    ws_password = self.ws_pw_strvar.get()
    
    proxy_addr = self.proxy_addr_strvar.get()
    proxy_code = self.proxy_code_strvar.get()
    
    self.conn_submit_strvar.set("Attempting to connect...")
    
    self.connection = psc.ProxiedServerConnection(ws_addr, ws_password, proxy_addr, proxy_code, lambda a: None)
    
    self.connected = await self.connection.connect()
    if not self.connected:
      return False
    
    return True
  
  def copy_proxy_url(self):
    self.root.clipboard_clear()
    self.root.clipboard_append(self.connection.proxy_url)
    
  def copy_room_code(self):
    self.root.clipboard_clear()
    self.root.clipboard_append(self.connection.roomcode)
    
  def setup_default_ui(self) -> None:
    self.defaultframe = ttk.Frame(self.root, padding = "5 5 5 5")
    self.defaultframe.place(relx = 0.5, rely = 0.5, anchor = tk.CENTER)
    
    self.copy_proxy_url_button = ttk.Button(self.defaultframe, text = "Copy proxy URL.", command = self.copy_proxy_url, style = "Huge.TButton")
    self.copy_proxy_url_button.grid(column = 0, row = 0, pady = (10, 10))
    
    self.copy_roomcode_button = ttk.Button(self.defaultframe, text = "Copy room code.", command = self.copy_room_code, style = "Huge.TButton")
    self.copy_roomcode_button.grid(column = 0, row = 1, pady = (10, 10))
    
if __name__ == '__main__':
  root = tk.Tk()
  client = ProxiedServerClient(root)
  
  _thread = threading.Thread(target=client.start_async_loop, daemon=True)
  _thread.start()
  
  root.mainloop()
  
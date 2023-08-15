import obswsgui
import tkinter as tk
import threading

if __name__ == '__main__':
  root = tk.Tk()
  client = obswsgui.OBS_WS_GUI(root)
  
  _thread = threading.Thread(target=client.start_async_loop, daemon=True)
  _thread.start()
  
  root.mainloop()
  
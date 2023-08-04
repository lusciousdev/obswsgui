from ui import *
import threading

if __name__ == '__main__':
  root = Tk()
  client = OBS_WS_GUI(root)
  
  _thread = threading.Thread(target=client.start_async_loop, daemon=True)
  _thread.start()
  
  root.mainloop()
  
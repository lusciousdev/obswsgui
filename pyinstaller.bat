python -m PyInstaller --onefile --windowed --name obswsgui .\src\main.py
python -m PyInstaller --onefile --windowed --name proxiedobswsclient .\src\proxiedclientgui.py
python -m PyInstaller --onefile --windowed --name proxiedobswsserver .\src\proxiedservergui.py

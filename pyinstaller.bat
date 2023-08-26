python -m PyInstaller --onefile --windowed --name obswsgui    .\obswsgui\__main__.py
python -m PyInstaller --onefile --windowed --name proxyclient .\obswsgui\client.py
python -m PyInstaller --onefile --windowed --name proxyserver .\obswsgui\server.py
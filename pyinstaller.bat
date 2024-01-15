python -m PyInstaller --onedir --windowed --name obswsgui    .\obswsgui\__main__.py
python -m PyInstaller --onedir --windowed --name proxyclient .\obswsgui\client.py
python -m PyInstaller --onedir --windowed --name proxyserver .\obswsgui\server.py
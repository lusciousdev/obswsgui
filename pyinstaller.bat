python -m PyInstaller --onedir --noconfirm --windowed --name obswsgui    .\obswsgui\__main__.py
python -m PyInstaller --onedir --noconfirm --windowed --name proxyclient .\obswsgui\client.py
python -m PyInstaller --onedir --noconfirm --windowed --name proxyserver .\obswsgui\server.py
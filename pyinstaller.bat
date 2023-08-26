python -m PyInstaller --onefile --windowed -d all --name obswsgui    .\obswsgui\__main__.py
python -m PyInstaller --onefile --windowed -d all --name proxyclient .\obswsgui\client.py
python -m PyInstaller --onefile --windowed -d all --name proxyserver .\obswsgui\server.py
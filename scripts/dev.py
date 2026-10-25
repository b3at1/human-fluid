"""One entry point; no model, cloud, or external assets needed at runtime."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
python=root/'backend/.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not python.exists():raise SystemExit('Run make setup first (or the explicit README installation commands).')
children=[]
def stop(*_):
    for p in children:
        if p.poll() is None:p.terminate()
    for p in children:
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill()
    raise SystemExit(0)
signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
try:
    children.append(subprocess.Popen([str(python),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--reload'],cwd=root/'backend'))
    children.append(subprocess.Popen(['npm.cmd' if os.name=='nt' else 'npm','run','dev'],cwd=root/'frontend'))
    print('Human Fluid → http://localhost:5173 (Ctrl+C stops both services)',flush=True)
    while all(p.poll() is None for p in children):time.sleep(.5)
finally:stop()

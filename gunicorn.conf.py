# gunicorn.conf.py
# Place this in the project root and run: gunicorn -c gunicorn.conf.py config.wsgi:application

import multiprocessing

# ── Binding ───────────────────────────────────────────────────────────────────
bind = "0.0.0.0:8000"

# ── Workers ───────────────────────────────────────────────────────────────────
# Rule of thumb: (2 × CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"          # stdout
errorlog  = "-"          # stderr
loglevel  = "info"

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "hub"

# ── Reload on code change (dev only — remove in prod) ─────────────────────────
# reload = True
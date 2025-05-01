import os
import sys
import random
import time
from pathlib import Path

DEBUG = bool(sys.platform == "win32")
if DEBUG:
    print("The app is running in DEBUG mode.")

if DEBUG:
    home_dir = str(Path.home())
    LOG_FILE = os.path.join(home_dir, "notebook_app.log")
else:
    LOG_FILE = "/var/log/notebook_app.log"
print(f"APP log will be written to this file: {LOG_FILE}")

# "redis://:{password}@{host}:{port}/{db}"
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    print("No REDIS_URL configured, global lock will not be used.")

STORAGE_ROOT = os.environ.get("STORAGE_ROOT")
if not STORAGE_ROOT:
    home_dir = str(Path.home())
    STORAGE_ROOT = os.path.join(home_dir, "notebook_storage_root")

BLOG_ROOT = os.path.join(STORAGE_ROOT, "blog")
for _try_time in range(5):
    try:
        os.makedirs(BLOG_ROOT, exist_ok=True)
        break
    except Exception:  # noqa
        time.sleep(random.random())

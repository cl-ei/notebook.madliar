import os
import random
import time

DEBUG = bool(os.environ.get("RUN_ENV") != "prod")

# "redis://:{password}@{host}:{port}/{db}"
REDIS_URL = os.environ.get("REDIS_URL")
STORAGE_ROOT = "./storage" if DEBUG else "/data/storage"
BLOG_ROOT = os.path.join(STORAGE_ROOT, "blog")
for _try_time in range(5):
    try:
        os.makedirs(BLOG_ROOT, exist_ok=True)
        break
    except Exception:  # noqa
        time.sleep(random.random())

print(F"REDIS_URL: {REDIS_URL}\nBLOG_ROOT: {BLOG_ROOT}")

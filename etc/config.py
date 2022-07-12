import os
print("-"*80)

CDN_URL = ""  # config["default"]["CDN_URL"]
PROJECT_ROOT = "./"

LOG_PATH = "/var/notebook/log"
os.makedirs(LOG_PATH, exist_ok=True)

APP_USERS_FOLDER_PATH = "/data/notebook_user"

REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port":  6379,
    "password": "redis",
    "db": 8,
}

print(
    "\n"
    "CONFIG: \n"
    f"CDN_URL: {CDN_URL}\n"
    f"PROJECT_ROOT: {PROJECT_ROOT}\n"
    f"LOG_PATH: {LOG_PATH}\n"
    f"APP_USERS_FOLDER_PATH: {APP_USERS_FOLDER_PATH}\n"
    f"REDIS_CONFIG: {REDIS_CONFIG}\n"
    f"{'-'*80}\n"
)

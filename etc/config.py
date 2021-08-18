import configparser

print("-"*80)

config = configparser.ConfigParser()
config.read('/etc/madliar.settings.ini')


CDN_URL = ""  # config["default"]["CDN_URL"]


try:
    PROJECT_ROOT = config["notebook"]["PROJECT_ROOT"]
except KeyError:
    PROJECT_ROOT = "./"

try:
    LOG_PATH = config["notebook"]["LOG_PATH"]
except KeyError:
    LOG_PATH = "./log"

try:
    APP_USERS_FOLDER_PATH = config["notebook"]["APP_USERS_FOLDER_PATH"]
except KeyError:
    APP_USERS_FOLDER_PATH = "./notebook_user"


REDIS_CONFIG = {}
try:
    REDIS_CONFIG["host"] = config["redis"]["host"]
    REDIS_CONFIG["port"] = int(config["redis"]["port"])
    REDIS_CONFIG["password"] = config["redis"]["password"]
    REDIS_CONFIG["db"] = int(config["redis"]["notebook_db"])
except KeyError:
    REDIS_CONFIG["host"] = "47.104.176.84"
    REDIS_CONFIG["port"] = 19941
    REDIS_CONFIG["password"] = ""
    REDIS_CONFIG["db"] = 8


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

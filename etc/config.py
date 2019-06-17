import configparser

try:
    config = configparser.ConfigParser()
    config.read('/etc/madliar.settings.ini')
except Exception as e:
    print("-"*80 + f"\nCannot load system configure file: {e}.\n")
    config = {}


try:
    CDN_URL = config["default"]["CDN_URL"]
except:
    CDN_URL = "https://statics.madliar.com"

try:
    PROJECT_ROOT = config["notebook"]["PROJECT_ROOT"]
except:
    PROJECT_ROOT = "./"

try:
    LOG_PATH = config["notebook"]["LOG_PATH"]
except:
    LOG_PATH = "./log"

try:
    APP_USERS_FOLDER_PATH = config["notebook"]["APP_USERS_FOLDER_PATH"]
except:
    APP_USERS_FOLDER_PATH = "./notebook_user"


REDIS_CONFIG = {}
try:
    REDIS_CONFIG["host"] = config["redis"]["host"]
    REDIS_CONFIG["port"] = config["redis"]["host"]
    REDIS_CONFIG["password"] = config["redis"]["host"]
except:
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
    "-"*80 + "\n"
)

import os


DEBUG = bool(os.environ.get("RUN_ENV") != "prod")

# "redis://:{password}@{host}:{port}/{db}"
REDIS_URL = os.environ.get("REDIS_URL")

print(F"REDIS_URL: {REDIS_URL}")

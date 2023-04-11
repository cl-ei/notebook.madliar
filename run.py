import os
import sys
import uvicorn
import logging
from src.config import DEBUG

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout),
    ],
)


if __name__ == "__main__":
    uvicorn.run("src.main:app", port=10091, host="0.0.0.0", workers=1 if DEBUG else 8)

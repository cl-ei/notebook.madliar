from app.handler import index, shared_page
from app.api_handler import handler as api_handler


user_url_map = (
    ("get", "/notebook", index),
    ("post", "/notebook/api", api_handler),
    ("get", "/notebook/{key}", shared_page),
)

static_url_map = (
    ("/static", "../madliar.com/static"),
)

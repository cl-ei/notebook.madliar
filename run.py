import sys
from aiohttp import web, web_urldispatcher
from app.middleware import installed_middlewares
from app.urls import user_url_map, static_url_map


router = web_urldispatcher.UrlDispatcher()
for method, url_pattern, handler in user_url_map:
    router.add_route(method, url_pattern, handler)

for prefix, path in static_url_map:
    router.add_static(prefix, path)


sys_args = sys.argv
if len(sys_args) < 3:
    host = "localhost"
    port = 10091
else:
    _, host, port = sys_args


sys.stdout.write("System start args: %s, %s\n" % (host, port))
app = web.Application(middlewares=installed_middlewares, router=router, debug=False)
web.run_app(
    app=app,
    host=host,
    port=int(port),
)

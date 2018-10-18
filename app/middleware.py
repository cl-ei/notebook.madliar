import traceback
from app.http import HttpResponse
from etc.log4 import logging


async def default_middle_ware(app, handler):
    async def wrapper(request):
        try:
            response = await handler(request)
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            reason = getattr(e, "reason", "Internal Server Error")
            if status_code == 500:
                error_message = str(e)
                traceback_info = traceback.format_exc()
                logging.error("Error happend: %s\n%s\n" % (error_message, traceback_info))
            content = "<center><h3>%s %s!</h3></center>" % (status_code, reason)
            response = HttpResponse(content, status=status_code, reason=reason)
        response.headers.add("Server", "madliar")
        return response
    return wrapper


installed_middlewares = [
    default_middle_ware,
]

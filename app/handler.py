import os
from app.http import render_to_response, HttpResponse, STATICS_FILE_MIME_TYPE
from etc.config import CDN_URL
from model import dao


async def index(request):
    mad_token = request.cookies.get("madToken")
    email = request.cookies.get("email")

    result = dao.check_login(email, mad_token)
    context = {"login_info": {"email": email}} if result else {}
    context["CDN_URL"] = CDN_URL
    return render_to_response(
        "templates/index.html",
        context=context
    )


def shared_page(request):
    key = request.match_info['key']
    path = dao.get_shared_file(key)
    if not path or not os.path.exists(path):
        return HttpResponse("Cannot find file: %s" % path, status=404)

    try:
        with open(path, "rb") as f:
            content = f.read()
    except Exception as e:
        # TODO: add log.
        return HttpResponse(str(e), status=500)

    base_name, ex_name = os.path.splitext(path)
    ex_name = ex_name.lstrip(".")

    content_type = "application/octet-stream"
    if not ex_name:
        content_type = "text/plain"
    elif ex_name.lower() in ("md", "markdown"):
        content_type = "text/plain"
    else:
        for ex, content_t in STATICS_FILE_MIME_TYPE:
            if ex_name in ex.split(" "):
                content_type = content_t
                break

    if not content_type.startswith("text"):
        return HttpResponse(content, content_type=content_type)

    if type(content) != str:
        try:
            content = content.decode("utf-8")
        except Exception:
            content = u"未能读取文件内容，其中含有不能识别的编码。"

    title = base_name.split("\\" if os.name in ("nt", ) else "/")[-1]
    context_data = {
        "title": title,
        "detail": content,
        "need_trans": ex_name.lower() in ("md", "markdown"),
        "CDN_URL": CDN_URL
    }
    return render_to_response("templates/share.html", context=context_data)

from aiohttp import web
from jinja2 import Template


STATICS_FILE_MIME_TYPE = (
    ("xml",             "text/xml"),
    ("css",             "text/css"),
    ("md, markdown",    "text/css"),
    ("html htm shtml",  "text/html"),
    ("txt",             "text/plain"),
    ("mml",             "text/mathml"),
    ("wml",             "text/vnd.wap.wml"),
    ("htc",             "text/x-component"),
    ("jad",             "text/vnd.sun.j2me.app-descriptor"),

    ("png",             "image/png"),
    ("gif",             "image/gif"),
    ("jpeg jpg",        "image/jpeg"),
    ("tif tiff",        "image/tiff"),
    ("webp",            "image/webp"),
    ("jng",             "image/x-jng"),
    ("ico",             "image/x-icon"),
    ("svg svgz",        "image/svg+xml"),
    ("bmp",             "image/x-ms-bmp"),
    ("wbmp",            "image/vnd.wap.wbmp"),

    ("mp4",             "video/mp4"),
    ("ts",              "video/mp2t"),
    ("mpeg mpg",        "video/mpeg"),
    ("3gpp 3gp",        "video/3gpp"),
    ("webm",            "video/webm"),
    ("mng",             "video/x-mng"),
    ("m4v",             "video/x-m4v"),
    ("flv",             "video/x-flv"),
    ("wmv",             "video/x-ms-wmv"),
    ("asx asf",         "video/x-ms-asf"),
    ("avi",             "video/x-msvideo"),
    ("mov",             "video/quicktime"),

    ("ogg",             "audio/ogg"),
    ("mp3",             "audio/mpeg"),
    ("mid midi kar",    "audio/midi"),
    ("m4a",             "audio/x-m4a"),
    ("ra",              "audio/x-realaudio"),

    ("js",              "application/javascript"),
    ("run",             "application/x-makeself"),
    ("xls",             "application/vnd.ms-excel"),
    ("jardiff",         "application/x-java-archive-diff"),
    ("rar",             "application/x-rar-compressed"),
    ("xpi",             "application/x-xpinstall"),
    ("sea",             "application/x-sea"),
    ("hqx",             "application/mac-binhex40"),
    ("sit",             "application/x-stuffit"),
    ("rtf",             "application/rtf"),
    ("kml",             "application/vnd.google-earth.kml+xml"),
    ("xhtml",           "application/xhtml+xml"),
    ("jnlp",            "application/x-java-jnlp-file"),
    ("ppt",             "application/vnd.ms-powerpoint"),
    ("atom",            "application/atom+xml"),
    ("m3u8",            "application/vnd.apple.mpegurl"),
    ("rss",             "application/rss+xml"),
    ("cco",             "application/x-cocoa"),
    ("jar war ear",     "application/java-archive"),
    ("tcl tk",          "application/x-tcl"),
    ("prc pdb",         "application/x-pilot"),
    ("woff",            "application/font-woff"),
    ("zip",             "application/zip"),
    ("doc",             "application/msword"),
    ("eot",             "application/vnd.ms-fontobject"),
    ("kmz",             "application/vnd.google-earth.kmz"),
    ("ps eps ai",       "application/postscript"),
    ("json",            "application/json"),
    ("pdf",             "application/pdf"),
    ("pl pm",           "application/x-perl"),
    ("7z",              "application/x-7z-compressed"),
    ("der pem crt",     "application/x-x509-ca-cert"),
    ("xspf",            "application/xspf+xml"),
    ("swf",             "application/x-shockwave-flash"),
    ("wmlc",            "application/vnd.wap.wmlc"),
    ("rpm",             "application/x-redhat-package-manager"),
    ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ("bin exe dll deb dmg iso img msi msp msm", "application/octet-stream"),
)


class HttpResponse(web.Response):
    def __init__(self, content, *args, **kwargs):
        if "content_type" not in kwargs:
            kwargs["content_type"] = "text/html"
        if "body" not in kwargs:
            kwargs["body"] = content
        super(HttpResponse, self).__init__(*args, **kwargs)


def render_to_response(template, context=None, request=None):
    try:
        with open(template, encoding="utf-8") as f:
            template_context = f.read()
    except IOError:
        template_context = "<center><h3>Template Does Not Existed!</h3></center>"

    template = Template(template_context)
    return HttpResponse(template.render(context or {}), content_type="text/html")

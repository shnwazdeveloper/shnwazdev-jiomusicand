import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_from_directory

import jiomusic


APP_NAME = "shnwazdev-jiomusicand"
APP_VERSION = "2.0.0"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def api_error(message, status_code=400, **extra):
    payload = {
        "ok": False,
        "error": {
            "message": message,
            "status": status_code,
        },
        "timestamp": utc_now(),
    }
    payload.update(extra)
    return jsonify(payload), status_code


def summarize(data):
    return {
        "songs": len(data.get("songs", [])),
        "albums": len(data.get("albums", [])),
        "playlists": len(data.get("playlists", [])),
    }


def search_response(legacy=False):
    query = (request.args.get("query") or request.args.get("q") or "").strip()
    include_details = parse_bool(request.args.get("details"), default=legacy)

    if not query:
        return api_error("Add a query parameter, for example ?query=slow motion", 400)

    try:
        data = jiomusic.song_search(query=query, include_details=include_details)
    except jiomusic.UpstreamError as exc:
        return api_error(str(exc), 502, query=query)
    except Exception:
        return api_error("Unexpected server error while searching music.", 500, query=query)

    if legacy:
        return jsonify(data)

    return jsonify(
        {
            "ok": True,
            "query": query,
            "details": include_details,
            "counts": summarize(data),
            "data": data,
            "timestamp": utc_now(),
        }
    )


@app.get("/")
@app.get("/docs")
def docs():
    return render_template(
        "index.html",
        app_name=APP_NAME,
        app_version=APP_VERSION,
        year=datetime.now().year,
    )


@app.get("/api/search")
def api_search():
    return search_response(legacy=False)


@app.get("/result")
@app.get("/result/")
def legacy_result():
    return search_response(legacy=True)


@app.get("/health")
@app.get("/api/health")
def health():
    check_upstream = parse_bool(request.args.get("upstream"))
    upstream = {"checked": False}

    if check_upstream:
        upstream = jiomusic.check_upstream()

    status_code = 200 if upstream.get("ok", True) else 503
    return (
        jsonify(
            {
                "ok": status_code == 200,
                "service": APP_NAME,
                "version": APP_VERSION,
                "status": "healthy" if status_code == 200 else "degraded",
                "upstream": upstream,
                "endpoints": {
                    "docs": "/docs",
                    "health": "/api/health",
                    "search": "/api/search?query=slow%20motion",
                    "legacy": "/result/?query=slow%20motion",
                },
                "timestamp": utc_now(),
            }
        ),
        status_code,
    )


@app.get("/styles.css")
def styles():
    return send_from_directory("public", "styles.css")


@app.get("/app.js")
def script():
    return send_from_directory("public", "app.js")


@app.get("/favicon.svg")
def favicon():
    return send_from_directory("public", "favicon.svg")


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return api_error("Endpoint not found.", 404)
    return render_template(
        "index.html",
        app_name=APP_NAME,
        app_version=APP_VERSION,
        year=datetime.now().year,
    ), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5575))
    app.run(host="0.0.0.0", port=port, threaded=True)

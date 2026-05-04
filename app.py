import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_from_directory

import jiomusic


APP_NAME = "shnwazdev-jiomusicand"
APP_VERSION = "2.1.0"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

API_ENDPOINTS = [
    {
        "method": "GET",
        "path": "/",
        "title": "Home",
        "description": "Documentation homepage and live browser console.",
        "example": "/",
    },
    {
        "method": "GET",
        "path": "/docs",
        "title": "Documentation",
        "description": "Clean browser documentation page with live search testing and every endpoint listed.",
        "example": "/docs",
    },
    {
        "method": "GET",
        "path": "/api",
        "title": "API index",
        "description": "Service metadata, available routes, and example URLs.",
        "example": "/api",
    },
    {
        "method": "GET",
        "path": "/api/health",
        "title": "Health",
        "description": "Runtime status for uptime checks. Add upstream=true to test the live music upstream. Alias: /health.",
        "example": "/api/health?upstream=true",
    },
    {
        "method": "GET",
        "path": "/health",
        "title": "Health alias",
        "description": "Short alias for /api/health with the same response shape.",
        "example": "/health?upstream=true",
    },
    {
        "method": "GET",
        "path": "/api/search",
        "title": "All search results",
        "description": "Combined search results for songs, albums, playlists, artists, top results, shows, and episodes.",
        "example": "/api/search?query=slow%20motion",
    },
    {
        "method": "GET",
        "path": "/api/songs",
        "title": "Songs",
        "description": "Song-only search results with title, artist, image, preview URL, web URL, and language.",
        "example": "/api/songs?query=slow%20motion",
    },
    {
        "method": "GET",
        "path": "/api/albums",
        "title": "Albums",
        "description": "Album-only search results with artwork, title, subtitle, album ID, and web URL.",
        "example": "/api/albums?query=slow%20motion",
    },
    {
        "method": "GET",
        "path": "/api/playlists",
        "title": "Playlists",
        "description": "Playlist-only search results from the upstream autocomplete source.",
        "example": "/api/playlists?query=bollywood",
    },
    {
        "method": "GET",
        "path": "/api/artists",
        "title": "Artists",
        "description": "Artist-only search results with role, image, and web URL.",
        "example": "/api/artists?query=arijit%20singh",
    },
    {
        "method": "GET",
        "path": "/api/top",
        "title": "Top results",
        "description": "Best upstream match for a query. Usually a song, album, artist, or playlist.",
        "example": "/api/top?query=slow%20motion",
    },
    {
        "method": "GET",
        "path": "/api/shows",
        "title": "Shows",
        "description": "Show-only search results when the upstream returns podcast or show matches.",
        "example": "/api/shows?query=music",
    },
    {
        "method": "GET",
        "path": "/api/episodes",
        "title": "Episodes",
        "description": "Episode-only search results when the upstream returns playable episode matches.",
        "example": "/api/episodes?query=music",
    },
    {
        "method": "GET",
        "path": "/api/raw/autocomplete",
        "title": "Raw autocomplete",
        "description": "Unmodified upstream autocomplete JSON for debugging or custom clients.",
        "example": "/api/raw/autocomplete?query=slow%20motion",
    },
    {
        "method": "GET",
        "path": "/result/",
        "title": "Legacy result",
        "description": "Compatibility route for older clients from the original JioMusicAPI project.",
        "example": "/result/?query=slow%20motion",
    },
]


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
        key: len(value)
        for key, value in data.items()
        if isinstance(value, list)
    }


def endpoint_payload():
    return [
        {
            **endpoint,
            "url": endpoint["example"],
        }
        for endpoint in API_ENDPOINTS
    ]


def get_query():
    return (request.args.get("query") or request.args.get("q") or "").strip()


def search_response(legacy=False):
    query = get_query()
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


def category_response(category, public_name=None):
    query = get_query()
    include_details = parse_bool(request.args.get("details"))

    if not query:
        return api_error("Add a query parameter, for example ?query=slow motion", 400)

    try:
        data = jiomusic.song_search(query=query, include_details=include_details)
    except jiomusic.UpstreamError as exc:
        return api_error(str(exc), 502, query=query, category=public_name or category)
    except Exception:
        return api_error(
            "Unexpected server error while searching music.",
            500,
            query=query,
            category=public_name or category,
        )

    items = data.get(category, [])
    return jsonify(
        {
            "ok": True,
            "query": query,
            "category": public_name or category,
            "count": len(items),
            "data": items,
            "timestamp": utc_now(),
        }
    )


def raw_autocomplete_response():
    query = get_query()

    if not query:
        return api_error("Add a query parameter, for example ?query=slow motion", 400)

    try:
        data = jiomusic.raw_autocomplete(query=query)
    except jiomusic.UpstreamError as exc:
        return api_error(str(exc), 502, query=query)

    return jsonify(
        {
            "ok": True,
            "query": query,
            "source": "jiosaavn.autocomplete.get",
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
        endpoints=API_ENDPOINTS,
        year=datetime.now().year,
    )


@app.get("/api")
@app.get("/api/")
def api_index():
    return jsonify(
        {
            "ok": True,
            "service": APP_NAME,
            "version": APP_VERSION,
            "docs": "/docs",
            "endpoints": endpoint_payload(),
            "timestamp": utc_now(),
        }
    )


@app.get("/api/search")
def api_search():
    return search_response(legacy=False)


@app.get("/api/songs")
@app.get("/api/song")
def api_songs():
    return category_response("songs", "songs")


@app.get("/api/albums")
@app.get("/api/album")
def api_albums():
    return category_response("albums", "albums")


@app.get("/api/playlists")
@app.get("/api/playlist")
def api_playlists():
    return category_response("playlists", "playlists")


@app.get("/api/artists")
@app.get("/api/artist")
def api_artists():
    return category_response("artists", "artists")


@app.get("/api/top")
@app.get("/api/topquery")
def api_top():
    return category_response("topquery", "top")


@app.get("/api/shows")
@app.get("/api/show")
def api_shows():
    return category_response("shows", "shows")


@app.get("/api/episodes")
@app.get("/api/episode")
def api_episodes():
    return category_response("episodes", "episodes")


@app.get("/api/raw/autocomplete")
def api_raw_autocomplete():
    return raw_autocomplete_response()


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
                "endpoints": endpoint_payload(),
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
        endpoints=API_ENDPOINTS,
        year=datetime.now().year,
    ), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5575))
    app.run(host="0.0.0.0", port=port, threaded=True)

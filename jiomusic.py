from html import unescape
from urllib.parse import quote_plus

import requests


SEARCH_URL = "http://beatsapi.media.jio.com/v2_1/beats-api/jio/src/response/search2/{query}/"
JIOSAAVN_URL = "https://www.jiosaavn.com/api.php"
PLAYLIST_URL = "http://beatsapi.media.jio.com/v2_1/beats-api/jio/src/response/listsongs/playlistsongs/{id}"
ALBUM_URL = "http://beatsapi.media.jio.com/v2_1/beats-api/jio/src/response/albumsongs/albumid/{id}"
STREAM_URL = "http://jiobeats.cdn.jio.com/mod/_definst_/mp4:hdindiamusic/audiofiles/{folder}/{album}/{id}_{bitrate}.mp4/playlist.m3u8"
TIMEOUT = (4, 16)

session = requests.Session()
session.headers.update(
    {
        "Accept": "application/json",
        "User-Agent": "shnwazdev-jiomusicand/2.0",
    }
)


class UpstreamError(RuntimeError):
    pass


def fetch_json(url, params=None):
    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.Timeout as exc:
        raise UpstreamError("JioMusic upstream timed out. Try again in a moment.") from exc
    except requests.RequestException as exc:
        raise UpstreamError("JioMusic upstream request failed.") from exc
    except ValueError as exc:
        raise UpstreamError("JioMusic upstream returned an invalid response.") from exc


def ensure_ok(results):
    code = results.get("messageCode")
    if str(code) != "200":
        raise UpstreamError(f"JioMusic upstream returned messageCode {code or 'unknown'}.")


def image_url(base_image_url, image):
    if not image:
        return None
    return f"{base_image_url}{str(image).replace('400x400', '800x800')}"


def saavn_image_url(image):
    if not image:
        return None
    return str(image).replace("50x50", "500x500").replace("150x150", "500x500")


def get_stream_link(song_id, bitrate=320):
    parts = str(song_id).split("_")
    if len(parts) < 2:
        return None
    return STREAM_URL.format(folder=parts[0], album=parts[1], id=song_id, bitrate=bitrate)


def format_song(song, base_image_url):
    song_id = song.get("id")
    return {
        "id": song_id,
        "title": song.get("title"),
        "artist": song.get("artist"),
        "subtitle": song.get("subtitle"),
        "image": image_url(base_image_url, song.get("image")),
        "url": get_stream_link(song_id),
        "s_order": song.get("s_order"),
        "type": song.get("type"),
        "albumid": song.get("albumid"),
    }


def format_collection(item, base_image_url, collection_type, include_details=False):
    collection_id = item.get("id")
    payload = {
        "id": collection_id,
        "title": item.get("title"),
        "subtitle": item.get("subtitle"),
        "image": image_url(base_image_url, item.get("image")),
        "type": item.get("type"),
        "songCount": item.get("songCount"),
    }

    if collection_type == "album":
        payload["albumid"] = item.get("albumid")
    else:
        payload["playlistid"] = item.get("playlistid")

    if include_details and collection_id:
        details = album_details(collection_id) if collection_type == "album" else playlist_details(collection_id)
        payload["label"] = details.get("header", {}).get("label")
        songs_key = "album_songs" if collection_type == "album" else "playlist_songs"
        payload[songs_key] = [
            format_song(song, base_image_url) for song in details.get("list", [])
        ]

    return payload


def clean(value):
    if value is None:
        return None
    return unescape(str(value))


def format_saavn_song(song):
    more_info = song.get("more_info", {})
    return {
        "id": song.get("id"),
        "title": clean(song.get("title")),
        "artist": clean(more_info.get("primary_artists") or more_info.get("singers")),
        "subtitle": clean(song.get("album") or song.get("description")),
        "image": saavn_image_url(song.get("image")),
        "url": more_info.get("vlink") or song.get("url"),
        "web_url": song.get("url"),
        "s_order": song.get("position"),
        "type": song.get("type"),
        "albumid": None,
        "language": more_info.get("language"),
    }


def format_saavn_collection(item, collection_type):
    payload = {
        "id": item.get("id"),
        "title": clean(item.get("title")),
        "subtitle": clean(item.get("description") or item.get("music")),
        "image": saavn_image_url(item.get("image")),
        "type": item.get("type") or collection_type,
        "songCount": item.get("song_count") or item.get("songCount"),
        "web_url": item.get("url"),
    }

    if collection_type == "album":
        payload["albumid"] = item.get("id")
    else:
        payload["playlistid"] = item.get("id")

    return payload


def legacy_song_search(query, include_details=False):
    normalized_query = quote_plus((query or "").strip())
    if not normalized_query:
        return {"songs": [], "albums": [], "playlists": []}

    results = fetch_json(SEARCH_URL.format(query=normalized_query))
    ensure_ok(results)

    result = results.get("result", {})
    data = result.get("data", {})
    base_image_url = result.get("imageurl", "")

    return {
        "songs": [format_song(song, base_image_url) for song in data.get("Songs", [])],
        "albums": [
            format_collection(album, base_image_url, "album", include_details=include_details)
            for album in data.get("Albums", [])
        ],
        "playlists": [
            format_collection(playlist, base_image_url, "playlist", include_details=include_details)
            for playlist in data.get("Playlists", [])
        ],
    }


def saavn_song_search(query):
    results = fetch_json(
        JIOSAAVN_URL,
        params={
            "__call": "autocomplete.get",
            "_format": "json",
            "_marker": "0",
            "query": query,
        },
    )

    return {
        "songs": [
            format_saavn_song(song)
            for song in results.get("songs", {}).get("data", [])
        ],
        "albums": [
            format_saavn_collection(album, "album")
            for album in results.get("albums", {}).get("data", [])
        ],
        "playlists": [
            format_saavn_collection(playlist, "playlist")
            for playlist in results.get("playlists", {}).get("data", [])
        ],
    }


def song_search(query, include_details=False):
    try:
        return legacy_song_search(query, include_details=include_details)
    except UpstreamError:
        return saavn_song_search(query)


def playlist_details(playlist_id):
    results = fetch_json(PLAYLIST_URL.format(id=playlist_id))
    ensure_ok(results)
    return results.get("result", {}).get("data", {})


def album_details(album_id):
    results = fetch_json(ALBUM_URL.format(id=album_id))
    ensure_ok(results)
    return results.get("result", {}).get("data", {})


def check_upstream():
    try:
        song_search("slow motion", include_details=False)
    except UpstreamError as exc:
        return {"checked": True, "ok": False, "message": str(exc)}
    return {"checked": True, "ok": True}

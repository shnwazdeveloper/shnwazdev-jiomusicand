# shnwazdev-jiomusicapi

Clean Flask API and documentation website for the legacy JioMusic search API. This repo is based on `cyberboysumanjay/JioMusicAPI` and modernized for local development and Vercel deployment.

Repository: `shnwazdeveloper/shnwazdev-jiomusicapi`

## What is included

- Documentation homepage at `/` and `/docs`
- Endpoint index at `/api`
- Fast uptime endpoint at `/api/ping`
- Modern search endpoint at `/api/search`
- Compact search summary endpoint at `/api/summary`
- Category endpoints for songs, albums, playlists, artists, top results, shows, and episodes
- Raw autocomplete endpoint at `/api/raw/autocomplete`
- Deployment diagnostics endpoint at `/api/diagnostics`
- Health endpoints at `/api/health` and `/health`
- Legacy compatibility route at `/result/`
- Vercel-ready Flask entrypoint in `app.py`
- Local development port set to `5575`

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PORT = "5575"
python app.py
```

Open `http://localhost:5575`.

Run the smoke test:

```powershell
python scripts/smoke_test.py
```

## API

All endpoints accept `query` or `q` where search text is needed.

### Ping

```http
GET /api/ping
```

Returns a fast no-upstream `pong` response for uptime monitors.

### Endpoint index

```http
GET /api
```

Returns service metadata and every documented endpoint.

### Search all categories

```http
GET /api/search?query=slow%20motion
```

Optional parameters:

- `query` or `q`: song, album, artist, playlist, show, or episode search text
- `details=true`: include album and playlist track lists

### Search summary

```http
GET /api/summary?query=slow%20motion
```

Returns counts, the top result, and every upstream item for each category by default. `limit` is optional and has no server-side maximum; use `limit=3` only when you want a smaller preview. You can also use `limit=all`, `limit=unlimited`, or `limit=0` to request every available item explicitly.

### Category endpoints

```http
GET /api/songs?query=slow%20motion
GET /api/albums?query=slow%20motion
GET /api/playlists?query=bollywood
GET /api/artists?query=arijit%20singh
GET /api/top?query=slow%20motion
GET /api/shows?query=music
GET /api/episodes?query=music
```

Each category endpoint returns:

```json
{
  "ok": true,
  "query": "slow motion",
  "category": "songs",
  "count": 5,
  "data": []
}
```

### Health

```http
GET /api/health
```

Use `upstream=true` to include a live upstream check:

```powershell
curl "http://localhost:5575/api/health?upstream=true"
```

### Raw autocomplete

```http
GET /api/raw/autocomplete?query=slow%20motion
```

Returns the unmodified upstream autocomplete response.

### Deployment diagnostics

```http
GET /api/diagnostics
```

Checks Python, Vercel environment markers, required files, public assets, and endpoint count without exposing secrets.

### Legacy route

```http
GET /result/?query=slow%20motion
```

This keeps old clients working by returning the raw payload.

## Deploy to Vercel

Vercel can detect the Flask app from the root `app.py` file and install `requirements.txt`. The project also includes `vercel.json`, `.vercelignore`, and `.python-version` for predictable Vercel hosting.

The `vercel.json` file intentionally does not define `functions.app.py`. Root Flask apps are handled by Vercel's Flask framework detection, while the `functions` property only targets function files such as files inside `/api`.

```powershell
npx vercel@latest
```

For production:

```powershell
npx vercel@latest --prod
```

After deployment, check:

```text
https://your-project.vercel.app/api/health
https://your-project.vercel.app/api/ping
https://your-project.vercel.app/api/diagnostics
https://your-project.vercel.app/api/search?query=slow%20motion
https://your-project.vercel.app/api
```

## Notes

The original JioMusic `beatsapi.media.jio.com` endpoint is legacy and may fail or return unavailable responses. The app now falls back to JioSaavn autocomplete so search stays usable, and it returns clear JSON errors if every upstream is unavailable.

## Attribution

Original project: `cyberboysumanjay/JioMusicAPI`

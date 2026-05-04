# shnwazdev-jiomusicand

Clean Flask API and documentation website for the legacy JioMusic search API. This repo is based on `cyberboysumanjay/JioMusicAPI` and modernized for local development and Vercel deployment.

## What is included

- Documentation homepage at `/` and `/docs`
- Modern search endpoint at `/api/search`
- Health endpoint at `/api/health`
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

## API

### Search

```http
GET /api/search?query=slow%20motion
```

Optional parameters:

- `query` or `q`: song, album, or playlist search text
- `details=true`: include album and playlist track lists

Example:

```powershell
curl "http://localhost:5575/api/search?query=slow%20motion"
```

### Health

```http
GET /api/health
```

Use `upstream=true` to include a live upstream check:

```powershell
curl "http://localhost:5575/api/health?upstream=true"
```

### Legacy route

```http
GET /result/?query=slow%20motion
```

This keeps old clients working by returning the raw payload.

## Deploy to Vercel

Vercel can detect the Flask app from `app.py` and install `requirements.txt`.

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
https://your-project.vercel.app/api/search?query=slow%20motion
```

## Notes

The original JioMusic `beatsapi.media.jio.com` endpoint is legacy and may fail or return unavailable responses. The app now falls back to JioSaavn autocomplete so search stays usable, and it returns clear JSON errors if every upstream is unavailable.

## Attribution

Original project: `cyberboysumanjay/JioMusicAPI`

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402


CHECKS = [
    ("/", 200),
    ("/docs", 200),
    ("/api", 200),
    ("/api/ping", 200),
    ("/api/diagnostics", 200),
    ("/api/health", 200),
    ("/health", 200),
    ("/api/search?query=slow%20motion", 200),
    ("/api/summary?query=slow%20motion&limit=2", 200),
    ("/api/songs?query=slow%20motion", 200),
    ("/api/albums?query=slow%20motion", 200),
    ("/api/playlists?query=bollywood", 200),
    ("/api/artists?query=arijit%20singh", 200),
    ("/api/top?query=slow%20motion", 200),
    ("/api/raw/autocomplete?query=slow%20motion", 200),
    ("/result/?query=slow%20motion", 200),
]


def main():
    failures = []
    results = []

    with app.test_client() as client:
        for path, expected_status in CHECKS:
            response = client.get(path)
            ok = response.status_code == expected_status
            results.append(
                {
                    "path": path,
                    "status": response.status_code,
                    "ok": ok,
                }
            )
            if not ok:
                failures.append(f"{path} returned {response.status_code}, expected {expected_status}")

        api_payload = client.get("/api").get_json()
        diagnostics_payload = client.get("/api/diagnostics").get_json()
        if api_payload.get("service") != "shnwazdev-jiomusicapi":
            failures.append("/api returned an unexpected service name")
        if len(api_payload.get("endpoints", [])) < 18:
            failures.append("/api returned fewer endpoints than expected")
        if not all(diagnostics_payload.get("required_files", {}).values()):
            failures.append("/api/diagnostics reported missing required files")
        if not all(diagnostics_payload.get("public_assets", {}).values()):
            failures.append("/api/diagnostics reported missing public assets")

    print(json.dumps({"ok": not failures, "results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

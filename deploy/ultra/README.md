# Ultra.cc deployment

MykoKnoks can run on an Ultra.cc shared app slot without Docker or root privileges.

## Target

- SSH user: `knoksen`
- Ultra host: `nova.usbx.me`
- Public proxy path: `/mykoknoks-api`
- Public API URL: `https://knoksen.nova.usbx.me/mykoknoks-api`
- Android origin allowed by CORS: `https://appassets.androidplatform.net`

## Ultra constraints

Ultra custom applications must run in the user's home directory, must not require sudo/root, and must bind only to a port assigned to the service. Ultra exposes assigned/free ports through `app-ports` and supports user-level systemd plus custom Nginx proxy snippets.

MykoKnoks deliberately follows that model: Python venv + `systemctl --user` + `~/.apps/nginx/proxy.d`.

## Install

From the repository checkout on the Ultra slot:

```bash
bash deploy/ultra/install.sh
```

The installer calls `app-ports free` and automatically selects the first free 5-digit assigned port. You can still explicitly choose one of your free assigned ports:

```bash
bash deploy/ultra/install.sh 12345
```

Do not supply a port unless it is listed by `app-ports free`.

The installer:

1. detects and validates an Ultra-assigned port;
2. creates a Python virtual environment under `~/.local/share/mykoknoks/venv`;
3. installs the FastAPI backend in that venv;
4. creates `~/.local/share/mykoknoks/features.sqlite` as the lightweight H3 feature store;
5. configures `DATABASE_URL=sqlite:///.../features.sqlite` for Store mode;
6. creates a user-level `mykoknoks.service`;
7. configures FastAPI `ROOT_PATH=/mykoknoks-api` for correct reverse-proxy URL generation;
8. creates `~/.apps/nginx/proxy.d/mykoknoks.conf`;
9. restarts the Ultra Nginx service with `app-nginx restart`;
10. starts/enables MykoKnoks with `systemctl --user`;
11. tests both local `/health` and the public HTTPS proxy;
12. saves deployment metadata to `~/.local/share/mykoknoks/deployment.env`.

## Verify

Run the status helper:

```bash
bash deploy/ultra/status.sh
```

It reports service state, local/public health, SQLite path/size, H3 feature count, evidence count and recent logs.

Or manually:

```bash
systemctl --user status mykoknoks.service --no-pager
cat ~/.local/share/mykoknoks/deployment.env
curl -fsS https://knoksen.nova.usbx.me/mykoknoks-api/health
```

Expected health response contains `status: ok`, `service: MykoKnoks`, the deployed version and `root_path: /mykoknoks-api`.

## Android connection

Android v0.2.3+ no longer hardcodes one backend at compile time. In the app, open **Server connection**, keep or enter:

```text
https://knoksen.nova.usbx.me/mykoknoks-api
```

Tap **Test & connect**. Live and H3 Store modes remain disabled until the HTTPS health check succeeds. Demo scores and H3 cells run locally on-device; the current MapLibre basemap still needs internet access.

## Populate the H3 feature store

The SQLite store starts empty. Build a bounded real-data H3 snapshot first:

```bash
~/.local/share/mykoknoks/venv/bin/python scripts/ingest_live_features.py \
  --lat 58.735 --lon 5.647 \
  --radius-km 1 \
  --resolution 9 \
  --out data/jaren.jsonl
```

For a faster terrain-focused first ingest:

```bash
~/.local/share/mykoknoks/venv/bin/python scripts/ingest_live_features.py \
  --lat 58.735 --lon 5.647 \
  --radius-km 1 \
  --resolution 9 \
  --fast \
  --out data/jaren-fast.jsonl
```

Load the snapshot into Ultra's lightweight feature store:

```bash
~/.local/share/mykoknoks/venv/bin/python scripts/load_feature_store_lite.py \
  data/jaren.jsonl \
  --database ~/.local/share/mykoknoks/features.sqlite
```

Then verify row counts:

```bash
bash deploy/ultra/status.sh
```

The API reconstructs map geometry from each H3 index, so serving scalar environmental features does not require a spatial database extension. PostgreSQL remains supported by the repository and PostGIS remains the preferred option when a full spatial warehouse is available later.

## Store-mode request

After loading cells, verify the cached path directly:

```bash
curl -fsS 'https://knoksen.nova.usbx.me/mykoknoks-api/api/v1/cells?lat=58.735&lon=5.647&radius_km=1&resolution=9&data_mode=store'
```

Inspect `metadata.feature_store_backend`, `feature_store_hits`, `feature_store_total` and each cell's provenance. Cache misses remain visibly marked and never masquerade as measured environmental data.

## Logs

```bash
journalctl --user -u mykoknoks.service -n 100 --no-pager
```

Follow logs live:

```bash
journalctl --user -u mykoknoks.service -f
```

## Update

After pulling a newer repository version:

```bash
~/.local/share/mykoknoks/venv/bin/pip install -e ./backend
systemctl --user restart mykoknoks.service
bash deploy/ultra/status.sh
```

## Data modes on Ultra

- `demo`: H3 scores generated locally by Android/web UI; no MykoKnoks backend required.
- `live`: FastAPI queries bounded live Norwegian data adapters.
- `store`: FastAPI serves pre-ingested H3 features from SQLite on Ultra; the same repository layer also supports PostgreSQL.

The public path is stripped by Nginx before requests reach Uvicorn. FastAPI receives `ROOT_PATH=/mykoknoks-api`, which keeps OpenAPI and generated public URLs reverse-proxy aware.

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
4. creates a user-level `mykoknoks.service`;
5. configures FastAPI `ROOT_PATH=/mykoknoks-api` for correct reverse-proxy URL generation;
6. creates `~/.apps/nginx/proxy.d/mykoknoks.conf`;
7. restarts the Ultra Nginx service with `app-nginx restart`;
8. starts/enables MykoKnoks with `systemctl --user`;
9. tests both local `/health` and the public HTTPS proxy;
10. saves deployment metadata to `~/.local/share/mykoknoks/deployment.env`.

## Verify

Run the status helper:

```bash
bash deploy/ultra/status.sh
```

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

Tap **Test & connect**. Live and PostGIS modes remain disabled until the HTTPS health check succeeds. Demo mode always runs locally on-device, including when the server is offline.

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

- `demo`: generated locally by Android/web UI; does not require Ultra.
- `live`: FastAPI queries bounded live Norwegian data adapters; this is the first production target on Ultra.
- `store`: requires a reachable PostgreSQL/PostGIS database and a production `DATABASE_URL`. It intentionally remains unavailable until that database layer is deployed.

The public path is stripped by Nginx before requests reach Uvicorn. FastAPI receives `ROOT_PATH=/mykoknoks-api`, which keeps OpenAPI and generated public URLs reverse-proxy aware.

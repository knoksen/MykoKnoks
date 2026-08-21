# Ultra.cc deployment

MykoKnoks can run on an Ultra.cc shared app slot without Docker or root privileges.

## Target

- SSH user: `knoksen`
- Ultra host: `nova.usbx.me`
- Public proxy path: `/mykoknoks-api`
- Expected public API URL: `https://knoksen.nova.usbx.me/mykoknoks-api`

## Important Ultra constraints

Ultra custom applications must run in the user's home directory, must not require sudo/root, and must bind only to a port assigned to the service. Use `app-ports free` to select an unused port.

## Install

From the repository checkout on the Ultra slot:

```bash
bash deploy/ultra/install.sh <ASSIGNED_PORT>
```

Example only (do not use unless the port is actually assigned to your service):

```bash
bash deploy/ultra/install.sh 12345
```

The installer:

1. creates a Python virtual environment under `~/.local/share/mykoknoks/venv`;
2. installs the FastAPI backend in that venv;
3. creates a user-level systemd service;
4. creates `~/.apps/nginx/proxy.d/mykoknoks.conf`;
5. restarts the Ultra nginx service;
6. starts/enables MykoKnoks;
7. tests `/health` locally.

## Verify

```bash
systemctl --user status mykoknoks.service --no-pager
curl -fsS http://127.0.0.1:<ASSIGNED_PORT>/health
curl -fsS https://knoksen.nova.usbx.me/mykoknoks-api/health
```

## Logs

```bash
journalctl --user -u mykoknoks.service -n 100 --no-pager
```

## Update

After pulling a newer repository version:

```bash
~/.local/share/mykoknoks/venv/bin/pip install -e ./backend
systemctl --user restart mykoknoks.service
```

The initial Ultra deployment is intended for `demo` and bounded `live` API modes. `store` requires a reachable PostgreSQL/PostGIS database and should be enabled only after `DATABASE_URL` is configured for a production database.

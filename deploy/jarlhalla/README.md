# mykoknoks.jarlhalla.com deployment candidate

Public landing page: https://mykoknoks.jarlhalla.com/
Map application: https://mykoknoks.jarlhalla.com/app/
API base: https://mykoknoks.jarlhalla.com/mykoknoks-api

The existing landing page is retained. This candidate adds two paths. It does not change DNS, certificates, WordPress, other subdomains or the Ultra deployment. Local port 18180 must be free. The API has no public port; only the web proxy is bound to loopback.

## Preconditions and installation

Use the tested deployment branch (includes PR #28's MapLibre fix). The host must have Docker Compose and an existing HTTPS Nginx server for this exact hostname. Identify the active vhost with `sudo nginx -T` before changing any config. If the hostname is served by cPanel/Apache or another host, stop: this Nginx snippet cannot be applied there unchanged. Do not replace a default or shared server block. Confirm the existing landing page's document root and retain a backup of the exact vhost before edits.

From the repository root on the actual serving host:

```bash
docker compose -f deploy/jarlhalla/compose.yml config --quiet
docker compose -f deploy/jarlhalla/compose.yml build
docker compose -f deploy/jarlhalla/compose.yml up -d
curl --fail http://127.0.0.1:18180/mykoknoks-api/health
```

Copy `nginx.host.locations.conf` to a dedicated snippet and include it inside ONLY the existing HTTPS vhost for `mykoknoks.jarlhalla.com`. Check for conflicting locations first. Run `sudo nginx -t` and reload only if it succeeds. Never overwrite the existing site's config with the snippet. Add a link to `/app/` in the actual landing-page source after locating its publishing pipeline.

```bash
python3 deploy/jarlhalla/verify.py
```

Health success does not prove upstream adapters, populated store data or calibrated forecasts. SQLite volume is initially empty. Keep Demo labelled synthetic; verify Store data and live adapters separately. Do not automatically ingest or publish observations as part of deployment.

## Acceptance and rollback

Require landing page unchanged, `/app/` and real JS/CSS responses, JSON health at the correct root path, browser map/worker load, controls, server connection, and an explicit record of which data modes are verified. Until then status is **prepared, not deployed**.

Rollback: remove only the new include from the hostname's vhost, validate Nginx and reload. Stop the stack with `docker compose -f deploy/jarlhalla/compose.yml down`. Do not use `--volumes`: retain research data. The landing page should remain accessible throughout.

## Validation limits

Docker/Nginx runtime validation and installation require the serving host. The author's environment could not reach VPS SSH. Build success alone is not production acceptance. Keep this PR separate from operational evidence; record deployment commit, time and acceptance output after installation.

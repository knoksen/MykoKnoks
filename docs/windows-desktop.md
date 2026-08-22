# MykoKnoks Windows Desktop v0.3

MykoKnoks Desktop packages the existing React/MapLibre forecasting workspace as a native Windows x64 application using Electron. It is designed to connect directly to the deployed MykoKnoks HTTPS API while retaining the deterministic local H3 demo when the server is unavailable.

## Desktop capabilities

- Native Windows x64 installer (NSIS)
- Single-instance application shell
- Persistent window size and position
- Secure Electron renderer (`contextIsolation`, no Node integration, sandbox enabled)
- Native HTTP bridge for MykoKnoks API traffic, avoiding `file://` CORS problems without disabling Electron web security
- Automatic connection attempt to `https://knoksen.nova.usbx.me/mykoknoks-api`
- Live, H3 Store and local Demo modes
- MapLibre forecast map and H3 overlays
- Native Windows save dialogs
- Export current workspace to PDF
- Save current workspace as PNG screenshot
- Native menu with reload, zoom, fullscreen and developer tools
- External links open in the system browser
- Windows geolocation permission support when the runtime/provider makes a location available

## Development

From `frontend`:

```powershell
npm install
npm run desktop:dev
```

This starts Vite on localhost and launches Electron against the development renderer.

## Production build

On Windows:

```powershell
cd frontend
npm install
npm run desktop:build
```

The installer is written to:

```text
frontend/dist-desktop/MykoKnoks-Windows-Setup-v0.3.0-x64.exe
```

## GitHub Actions

`.github/workflows/windows-desktop.yml` builds the x64 NSIS installer on `windows-latest`, verifies that the EXE was produced, prints its SHA-256 hash, and uploads it as the `MykoKnoks-Windows-v0.3.0` workflow artifact.

The workflow disables automatic certificate discovery. The initial v0.3 installer is therefore expected to be unsigned unless a Windows code-signing setup is added later. Windows SmartScreen may warn about an unsigned first-party installer.

## API architecture

The renderer never receives Node.js access. API requests are passed through the restricted preload bridge to the Electron main process. The main process accepts only HTTP(S) URLs and returns response status/body to the renderer. This permits the packaged local renderer to use the remote FastAPI service without weakening `webSecurity`.

The default backend remains:

```text
https://knoksen.nova.usbx.me/mykoknoks-api
```

The desktop app performs a health check at startup. If the service is reachable it unlocks Live and H3 Store modes; otherwise the local H3 demo remains operational.

## Signing roadmap

For broad distribution, add an Authenticode code-signing certificate and feed the certificate to GitHub Actions through encrypted repository/environment secrets. Do not commit signing keys or certificate passwords to the repository.

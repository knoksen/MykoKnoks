# TODO_PROGRESS.md

Løpende utførelseslogg for Blackbox-arbeid.  
Alle oppgaver skal dokumentere status, testbevis og eventuelle blokkeringer.

---

## 2026-08-06 – Initial Engineering Handoff etablering

### Utført

- Opprettet Blackbox-handoff-dokumenter.
- La til enkel kjørbar prosjektstruktur med lokal Node-server, app-logikk og tester.

### Testbevis

- `npm test` → bestått, 3 tester.
- `npm run check` → bestått.

---

## 2026-08-06 – Thorough validation og policy-hardening v0.1.2

**Status:** Ferdig med dokumentert testmiljøbegrensning  
**Testet leveransecommit:** `da2508d18031c4ecbbac8da20731554393cf6f7a`  
**Branch:** `blackboxai/mycoterrain-handoff`  
**Opprinnelig gjenopprettet commit:** `8afb47dace82b1c7b14d1081b473900b285790c0`

### Verifisert avvik og tiltak

Gjennomgangen avdekket at den opprinnelige UI-knappen kunne endre `forecastEnabled` til `true` mens aktiv profil fortsatt var `Psilocybe semilanceata`. Dette brøt den dokumenterte P0-policyen.

Tiltak:

- Sentraliserte kontrollert-art-policyen i `src/mycel.js`.
- Håndhevet policyen ved både forecast-toggle og artsskifte i `app.js`.
- Deaktiverte forecast-kontrollen eksplisitt i UI for kontrollert art.
- La til normalisering av artsnavn for å hindre omgåelse med case eller mellomrom.
- Erstattet ekstern Unsplash-avhengighet med lokal SVG.
- Utvidet regresjonstestene fra 3 til 6.
- Gjorde `dist` og ZIP-pakken selvstendig testbare.

### Endrede filer

- `app.js`
- `src/mycel.js`
- `test/mycel.test.js`
- `index.html`
- `styles.css`
- `build.js`
- `package.json`
- `dist/**`
- `mycoterra-presentation.zip`
- `README.md`
- `BLACKBOX_START_HERE.md`
- `CHANGELOG.md`
- `TODO_BLACKBOX.md`
- `docs/KNOWN_ISSUES.md`

### Kvalitetspipeline

Tidligere Blackbox-baseline:

- Node.js `v24.18.0`
- npm `11.16.0`
- `npm run check` → bestått
- `npm test` → bestått, 3/3
- `npm run build` → bestått
- Post-build `check` og `test` → bestått

Uavhengig revalidering av v0.1.2:

- Node.js `v22.16.0`
- npm `10.9.2`
- `npm run check` → bestått
- `npm test` → bestått, 6/6
- `npm run build` → bestått
- Post-build `npm run check` → bestått
- Post-build `npm test` → bestått, 6/6
- I ekstrahert `dist`: `npm run check` og `npm test` → bestått, 6/6

### UI- og interaksjonstesting

Chromium-rendering ble gjennomført med prosjektets eksakte HTML/CSS og tilsvarende moduladferd ved desktop `1440 × 1000` og mobil `390 × 844`.

Bestått:

- Korrekt første rendering og tittel.
- Aktiv art vises som `Psilocybe semilanceata`.
- Forecast vises og forblir `false`.
- Policytekst er synlig og tilgjengelig via `aria-live`.
- Forecast-knappen er deaktivert og kan ikke endre tilstanden, heller ikke ved tvunget klikk.
- Tastaturfokus hopper over deaktivert kontroll og lander på `Refresh status`.
- Enter på refresh beholder sikker tilstand.
- Desktop-layout bruker to kolonner; mobil-layout én kolonne.
- Ingen horisontal overflow.
- Ingen console errors eller page errors i renderingskjøringen.
- Ingen eksterne bilde- eller asset-kall; lokal SVG lastes.

Ikke relevante funksjonstilstander i denne minimale demoen:

- Ingen søk, filter, backend, asynkron loading, tom datasamling eller dynamisk nettverksfeilflyt finnes ennå.

### Browserbegrensning

Direkte Chromium-navigasjon til lokal HTTP-server eller `file://` ble blokkert av testmiljøets administrative policy med `ERR_BLOCKED_BY_ADMINISTRATOR`. Derfor kunne full DevTools network-panel-inspeksjon av den serverte siden ikke gjennomføres i samme browserprosess.

Dette ble kompensert med:

- Separat HTTP-runtime-testing mot lokal Node-server.
- Chromium-rendering og faktisk kontrollinteraksjon via `page.set_content`.
- Statisk kontroll av alle lokale asset-referanser.

### HTTP-runtime

Kilde- og ZIP-runtime:

- `/` → HTTP 200, HTML, ikke-tom respons.
- Manglende fil → HTTP 404.
- Kodet traversal-forsøk → HTTP 404.
- `app.js`, `src/mycel.js` og `styles.css` → HTTP 200 med riktige innholdstyper.
- Ingen ubehandlede feil i serverens stderr.

### ZIP-validering

Fil: `mycoterra-presentation.zip`  
SHA-256: `2ed8b4248c379cf4f235f643013db6c337145efb0e6ffebb78e6760342c177b9`

Bestått:

- ZIP-integritet og ekstraksjon.
- Kun forventede runtime-, modul- og testfiler.
- Ingen `.git`, `node_modules`, miljøfiler, private nøkler, tokens, absolutte maskinbaner eller path traversal-navn.
- Hemmelighetsskann uten treff.
- Ekstrahert pakke bestod `check`, 6/6 tester og HTTP-smoketest.
- Midlertidig ekstraksjonsmappe ble ryddet.

### Policyverifikasjon

- `Psilocybe semilanceata` normaliseres og identifiseres som kontrollert profil.
- Effektiv `forecastEnabled` kan ikke bli `true` for profilen.
- Artsskifte til profilen nullstiller eventuell tidligere aktiv forecast.
- UI eksponerer ingen hotspot, innsamlingsrute, presis forekomst eller handlingsrettet prognose.

### Blokkeringer og risiko

- Direkte nettlesernavigasjon i testmiljøet er blokkert som beskrevet over.
- Demoen er ikke en vitenskapelig validert habitatmodell.
- APK/AAB, Windows-installer, backend, personvernfundament og produksjonsdata er fortsatt utsatt.

### Sluttverdict

**PASS WITH DOCUMENTED LIMITATIONS**

### Neste steg

- Gjenta direkte lokal-URL browser smoke test i et ubegrenset Windows-/CI-browsermiljø.
- Behold policytestene som obligatorisk quality gate ved all videre kart-, rute- eller forecast-utvikling.
- Fortsett med høyeste åpne P1-punkt i `TODO_BLACKBOX.md`.

---

## Mal for videre føring

### Dato – Oppgave-ID/Tittel

**Status:** Pågår / Ferdig / Blokkert

**Endrede filer:**
- `path/fil1`
- `path/fil2`

**Testbevis:**
- Kommando: `...`
- Resultat: Bestått/Feilet
- Notat: `...`

**Blokkeringer/Risiko:**
- `...`

**Neste steg:**
- `...`

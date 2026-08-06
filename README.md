# Mykoknoks / MycoTerrain

**MycoTerrain er klargjort for Blackbox AI 🚀**

Dette repoet inneholder en enkel, kjørbar prosjektstruktur for videre utvikling, kvalitetssikring og kontrollert leveranse.

## Formål

Gi Blackbox AI en komplett og operativ kontekst slik at videre arbeid kan utføres uten å rekonstruere prosjektets rammer, avgrensninger og prioriteringer.

## Innhold

- Minimal web-app med lokal Node-server
- Grunnleggende app-logikk for artsprofil og sikkerhetsregler
- Eksplisitt policyhåndheving for kontrollerte psykoaktive arter
- Lokal, selvstendig illustrasjon uten eksterne bildeavhengigheter
- Automatiserte tester, syntakskontroll og byggbar ZIP-presentasjon

## Start her

Les i denne rekkefølgen:

1. `BLACKBOX_START_HERE.md`
2. `BLACKBOX_MASTER_PROMPT.md`
3. `AGENTS.md`
4. `TODO_BLACKBOX.md`
5. `TODO_PROGRESS.md`
6. `docs/BLACKBOX_ACCEPTANCE_TESTS.md`
7. `docs/KNOWN_ISSUES.md`
8. `docs/OMITTED_AND_DEFERRED.md`
9. `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`

## Verifisert status – v0.1.2

- `npm run check` bestått
- `npm test` bestått: 6/6 tester
- `npm run build` bestått
- Post-build `check` og `test` bestått
- Desktop- og mobilrendering kontrollert i Chromium
- ZIP-integritet, innhold, hemmelighetsskann, ekstraksjon og runtime kontrollert
- Ekstrahert ZIP: `/` → 200, manglende fil → 404, traversal-forsøk → 404
- SHA-256 for validert ZIP dokumentert i leveranserapporten

## Viktige avgrensninger

Ikke inkludert i denne pakken:

- APK/AAB eller signert Windows-installer
- Produksjonsdatasett og vitenskapelig validert habitatmodell
- Backend, autentisering, synk og publisert personvern-/juridisk løsning
- Planlagte produktfunksjoner som offlinekart, eksport/import og AI-identifikasjon

Se full liste i `docs/OMITTED_AND_DEFERRED.md`.

## Kritisk sikkerhets- og etikkpolicy

Prosjektet inkluderer ikke funksjonalitet som gir handlingsrettet støtte for kontrollerte psykoaktive arter, herunder presise hotspots, innsamlingsruter eller prognoser.

`Psilocybe semilanceata` er en ikke-handlingsrettet informasjonsprofil med håndhevet:

- `forecastEnabled: false`

Regelen håndheves både i domenelogikken, app-tilstanden, UI-et og automatiserte regresjonstester.

## Videre arbeid

Prioritert backlog ligger i `TODO_BLACKBOX.md`. Løpende utførelse, testbevis og blokkeringer loggføres i `TODO_PROGRESS.md`.

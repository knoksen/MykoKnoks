# Mykoknoks / MycoTerrain

**MycoTerrain er klargjort for Blackbox AI 🚀**

Dette repoet er satt opp som en **v0.1.1 Engineering Handoff**-pakke for videre utvikling, kvalitetssikring og kontrollert leveranse.

## Formål

Gi Blackbox AI en komplett og operativ kontekst slik at videre arbeid kan utføres uten å rekonstruere prosjektets rammer, avgrensninger og prioriteringer.

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

## Verifisert status (handoff)

- 10 av 10 tester bestått (siste dokumenterte baseline)
- `npm run check` bestått
- JavaScript-syntakskontroll bestått
- JSON-validering bestått
- ZIP-integritet kontrollert uten feil
- SHA-256 generert

## Viktige avgrensninger

Ikke inkludert i denne pakken:

- Build/distribusjon-artefakter (bl.a. `package-lock.json`, `node_modules`, APK/AAB, Windows installer)
- Produksjonsdatasett og vitenskapelig validert habitatmodell
- Backend/autentisering/synk/personvern-juridisk publisering
- Flere planlagte produktfunksjoner (offlinekart, eksport/import, AI-identifikasjon m.m.)

Se full liste i `docs/OMITTED_AND_DEFERRED.md`.

## Kritisk sikkerhets- og etikkpolicy

Prosjektet inkluderer ikke funksjonalitet som gir handlingsrettet støtte for kontrollerte psykoaktive arter (presise hotspots, ruter, prognoser).

`Psilocybe semilanceata` skal forbli en ikke-handlingsrettet informasjonsprofil med:

- `forecastEnabled: false`

Se `SECURITY.md` og `AGENTS.md` for detaljer.

## Videre arbeid

Prioritert backlog ligger i `TODO_BLACKBOX.md` (P0–P3).  
Løpende utførelse, testbevis og blokkeringer loggføres i `TODO_PROGRESS.md`.

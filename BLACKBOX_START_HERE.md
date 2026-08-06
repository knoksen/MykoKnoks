# BLACKBOX_START_HERE.md

Velkommen til **MycoTerrain v0.1.2 – Engineering Handoff**.

Dette er én tydelig inngang til prosjektet for Blackbox AI. Målet er at Blackbox skal kunne åpne prosjektet, forstå avgrensningene og arbeide videre uten å rekonstruere kontekst.

## Leserekkefølge (obligatorisk)

1. `BLACKBOX_MASTER_PROMPT.md`
2. `AGENTS.md`
3. `TODO_BLACKBOX.md`
4. `TODO_PROGRESS.md`
5. `docs/BLACKBOX_ACCEPTANCE_TESTS.md`
6. `docs/KNOWN_ISSUES.md`
7. `docs/OMITTED_AND_DEFERRED.md`
8. `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`

## Prosjektstatus

- Versjon: **v0.1.2 Engineering Handoff**
- Tilstand: **Klargjort for videre Blackbox AI-arbeid**
- Tester: **6/6 bestått**
- Kvalitetssjekk: `npm run check` bestått
- Build: `npm run build` bestått
- ZIP: integritet, ekstraksjon, tester og runtime verifisert
- Policy: kontrollert artsprofil kan ikke aktivere forecast

## Viktige avgrensninger

Følgende er ikke inkludert i denne pakken:

- Signerte Android-/Windows-distribusjoner
- Produksjonsdata og vitenskapelig validert habitatmodell
- Backend, konto, autentisering eller synk
- Telemetri og full produksjonssikkerhetsrevisjon
- Avanserte produktfunksjoner som offlinekart, eksport/import, AI-identifikasjon og community

## Sikkerhets- og etikkmerknad

Prosjektet inkluderer ikke presise forekomstkart, hotspots, innsamlingsruter eller prognoser for kontrollerte psykoaktive arter.

`Psilocybe semilanceata` skal forbli en ikke-handlingsrettet informasjonsprofil med `forecastEnabled: false`. Dette håndheves i kode, UI og tester.

## Arbeidsregel for Blackbox

- Følg `AGENTS.md` strengt.
- Arbeid videre fra høyeste åpne prioritet i `TODO_BLACKBOX.md`.
- Logg alt arbeid fortløpende i `TODO_PROGRESS.md`.
- Lever sluttresultat i henhold til `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`.

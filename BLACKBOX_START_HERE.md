# BLACKBOX_START_HERE.md

Velkommen til **MycoTerrain v0.1.1 – Engineering Handoff**.

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

## Prosjektstatus (kort)

- Versjon: **v0.1.1 Engineering Handoff**
- Tilstand: **Klargjort for Blackbox AI**
- Teststatus (siste verifiserte): **10/10 bestått**
- Kvalitetssjekk: `npm run check` bestått
- JS-syntaks: bestått
- JSON-validering: bestått
- ZIP-integritet: bestått
- SHA-256: generert

## Viktige avgrensninger

Følgende er **ikke** inkludert i denne pakken (se detaljer i `docs/OMITTED_AND_DEFERRED.md`):

- Build/distribusjon-artefakter (`package-lock.json`, `node_modules`, Android build outputs, installerfiler)
- Produksjonsdata og vitenskapelig validert habitatmodell
- Backend-konto/autentisering/synk
- Telemetri, full sikkerhetsrevisjon og publiserte juridiske dokumenter
- Avanserte produktfunksjoner (offlinekart, eksport/import, AI-identifikasjon, community)

## Sikkerhets- og etikkmerknad

Prosjektet inkluderer **ikke** presise forekomstkart/hotspots/ruter/prognoser for kontrollerte psykoaktive arter.  
`Psilocybe semilanceata` skal forbli en ikke-handlingsrettet informasjonsprofil med `forecastEnabled: false`.

## Arbeidsregel for Blackbox

- Følg `AGENTS.md` strengt.
- Implementer P0 først i `TODO_BLACKBOX.md`.
- Logg alt arbeid fortløpende i `TODO_PROGRESS.md`.
- Lever sluttresultat i henhold til `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`.

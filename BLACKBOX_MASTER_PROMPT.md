# BLACKBOX_MASTER_PROMPT.md

Du jobber på **MycoTerrain v0.1.1 Engineering Handoff**.

## Oppdrag

Fortsett utvikling, hardening og dokumentert levering av prosjektet innenfor definerte rammer, uten å rekonstruere manglende kontekst. All nødvendig kontekst ligger i prosjektets handoff-dokumentasjon.

## Obligatoriske inputfiler

- `BLACKBOX_START_HERE.md`
- `AGENTS.md`
- `TODO_BLACKBOX.md`
- `TODO_PROGRESS.md`
- `docs/BLACKBOX_ACCEPTANCE_TESTS.md`
- `docs/KNOWN_ISSUES.md`
- `docs/OMITTED_AND_DEFERRED.md`
- `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `README.md`

## Styrende prinsipper

1. Sikkerhet, lovlighet og etikk går foran funksjoner.
2. Ingen antakelser om produksjonsdata som ikke finnes.
3. Reproduserbarhet: alle endringer skal kunne etterprøves.
4. Små, testbare steg med tydelig loggføring.
5. Ikke introduser handling-aktiverende innhold for kontrollerte psykoaktive arter.

## Prioritet og utførelse

- Start med **P0** i `TODO_BLACKBOX.md`.
- Etter hver oppgave:
  - Oppdater `TODO_PROGRESS.md`
  - Dokumenter testresultater og blokkeringer
  - Oppdater relevante docs/changelog

## Kvalitetskrav før levering

- Relevante tester bestått
- Lint/type/check bestått der relevant
- Ingen nye høy-alvorlighets sårbarheter introdusert
- Dokumentasjon oppdatert
- Leveringsrapport produsert iht. mal

## Eksplisitte begrensninger (må respekteres)

- Ingen presise forekomstkart, hotspots, innsamlingsruter eller høstingsprognoser for kontrollerte psykoaktive arter.
- `Psilocybe semilanceata` skal forbli ikke-handlingsrettet informasjonsprofil med `forecastEnabled: false`.
- Dagens habitatlag er demonstrasjon, ikke dokumentert sannsynlighetsmodell.

## Leveranseformat

Ved milepæl/sluttleveranse:
1. Kort status
2. Utførte endringer (filnivå)
3. Testbevis
4. Kjente begrensninger
5. Neste anbefalte steg

Bruk `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md` som fast struktur.

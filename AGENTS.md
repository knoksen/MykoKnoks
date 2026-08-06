# AGENTS.md

Dette dokumentet definerer faste regler for kode, testing, sikkerhet og rapportering i MycoTerrain-prosjektet.

## 1) Kodepraksis

- Bruk små, isolerte endringer.
- Unngå breaking changes uten eksplisitt dokumentasjon.
- Følg eksisterende navngivning og struktur.
- Ikke legg inn hardkodede hemmeligheter/tokens/API-nøkler.
- Dokumenter alle nye config-flagg og miljøvariabler.

## 2) Testing og kvalitet

Ved hver relevant endring:

- Kjør relevante enhetstester/integrasjonstester.
- Kjør prosjektets sjekker (`npm run check` eller tilsvarende).
- Bekreft at JS/JSON-syntaks og valideringer består.
- Legg testbevis i `TODO_PROGRESS.md`.

Minimum rapportering av testbevis:

- Kommando
- Resultat (bestått/feilet)
- Kort kommentar/blokkering

## 3) Sikkerhetskrav

- Ingen introduksjon av kjente høy-risiko sårbarheter.
- Valider input og håndter feil eksplisitt.
- Beskytt persondata; minst mulig innsamling.
- Ikke implementer funksjoner som muliggjør ulovlig aktivitet.
- Følg avgrensningene i `SECURITY.md` og `docs/OMITTED_AND_DEFERRED.md`.

## 4) Domenegrenser og etikk

Følgende er forbudt i dette prosjektet:

- Presise forekomstkart/hotspots for kontrollerte psykoaktive arter
- Innsamlingsruter og handlingsrettede høstingsprognoser
- Innhold som vesentlig øker misbruksrisiko

Krav:

- `Psilocybe semilanceata` skal forbli ikke-handlingsrettet profil
- `forecastEnabled: false` for denne arten

## 5) Arbeidsflyt

1. Les `BLACKBOX_START_HERE.md`
2. Prioriter `TODO_BLACKBOX.md` fra P0 til P3
3. Loggfør fortløpende i `TODO_PROGRESS.md`
4. Oppdater `CHANGELOG.md`
5. Lever status med rapportmalen i `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`

## 6) Rapportering

Hver leveranse skal inneholde:

- Hva som er gjort
- Hvilke filer som er endret
- Testbevis
- Kjente blokkeringer/risiko
- Neste anbefalte steg

Alt skal være etterprøvbart og konsistent med dokumentasjon i repoet.

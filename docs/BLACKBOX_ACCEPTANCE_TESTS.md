# BLACKBOX_ACCEPTANCE_TESTS.md

Konkrete akseptansekriterier for arbeid utført av Blackbox i dette prosjektet.

## A. Dokumentasjon og styring

### A1 – Startpunkt og styringsdokumenter finnes
**Kriterium:** Følgende filer finnes og er konsistente:
- `BLACKBOX_START_HERE.md`
- `BLACKBOX_MASTER_PROMPT.md`
- `AGENTS.md`
- `TODO_BLACKBOX.md`
- `TODO_PROGRESS.md`

**Pass når:** Alle filer eksisterer, peker til samme avgrensninger og prioritering.

### A2 – Omitted/deferred og kjente issues er oppdatert
**Kriterium:** `docs/OMITTED_AND_DEFERRED.md` og `docs/KNOWN_ISSUES.md` reflekterer reell status.
**Pass når:** Nye begrensninger eller avvik dokumenteres innen samme leveranse.

## B. Sikkerhet og etikk

### B1 – Ingen handlingsrettet støtte for kontrollerte psykoaktive arter
**Kriterium:** Ingen nye features/data/UI som muliggjør presise hotspots/ruter/prognoser.
**Pass når:** Kodegjennomgang og tester viser at dette ikke er introdusert.

### B2 – Psilocybe-policy håndheves
**Kriterium:** `Psilocybe semilanceata` er ikke-handlingsrettet profil med `forecastEnabled: false`.
**Pass når:** Konfig/data/tester bekrefter regelen.

## C. Kvalitet og testbarhet

### C1 – Relevante tester bestått
**Kriterium:** Endringer ledsages av relevante tester.
**Pass når:** Testkommandoer er kjørt og dokumentert i `TODO_PROGRESS.md`.

### C2 – Prosjektsjekk bestått
**Kriterium:** Prosjektets kvalitetssjekk (`npm run check` eller tilsvarende) passerer.
**Pass når:** Resultat loggføres med dato og kort kommentar.

### C3 – Ingen regresjon i dokumentert baseline
**Kriterium:** Tidligere verifiserte forhold (10/10 tester, syntaks/JSON/check) brytes ikke uten forklaring.
**Pass når:** Avvik enten ikke finnes eller er dokumentert som kjent blokkering.

## D. Leveransekrav

### D1 – Endringslogg oppdatert
**Kriterium:** `CHANGELOG.md` oppdateres for brukerrelevante eller tekniske endringer.
**Pass når:** Ny versjons-/arbeidsoppføring finnes.

### D2 – Fremdrift loggført
**Kriterium:** `TODO_PROGRESS.md` oppdateres med:
- endrede filer
- testbevis
- blokkeringer/risiko
- neste steg

**Pass når:** Oppføring finnes for hver levert endringspakke.

### D3 – Sluttrapport levert
**Kriterium:** Leveranse følger `docs/BLACKBOX_DELIVERY_REPORT_TEMPLATE.md`.
**Pass når:** Alle seksjoner er utfylt med etterprøvbar informasjon.

# TODO_BLACKBOX.md

Prioritert backlog for Blackbox-arbeid på MycoTerrain.

## P0 – Kritisk

- [x] Verifiser at avgrensninger for kontrollerte psykoaktive arter håndheves i data/config/UI
- [x] Bekreft og dokumenter at `Psilocybe semilanceata` har `forecastEnabled: false`
- [x] Etabler/forbedre testdekning for sikkerhetskritiske regler
- [x] Gjennomfør baseline sikkerhetsgjennomgang og loggfør funn
- [x] Oppdater dokumentasjon for dagens demonstrasjonsstatus av habitatmodell

## P1 – Høy prioritet

- [x] Stabiliser kvalitetspipeline (`check`/`test`/`build`) for reproduserbar kjøring
- [ ] Reduser øvrige tekniske svakheter i `docs/KNOWN_ISSUES.md`
- [ ] Forbedre generell feilhåndtering og inputvalidering i sentrale flyter
- [x] Oppdater README med tydelig skille mellom demo og produksjonsklart

## P2 – Middels prioritet

- [ ] Forbedre utvikleropplevelse med flere scripts og bedre feilmeldinger
- [ ] Legg til flere akseptansetester iht. `docs/BLACKBOX_ACCEPTANCE_TESTS.md`
- [ ] Stram inn fremtidig konfigurasjonsstyring og miljøvariabler
- [ ] Forbered struktur for fremtidig backend-integrasjon uten full backend

## P3 – Videre arbeid

- [ ] Vurder internasjonalisering (nb/en)
- [ ] Planlegg import/eksport-format (GeoJSON/CSV) på spesifikasjonsnivå
- [ ] Forbered roadmap for offlinekart og synk
- [ ] Dokumenter observability/telemetri med personvern som premiss

## Arbeidsregel

- Fullfør høyest prioritet først.
- Hver oppgave skal gi spor i `TODO_PROGRESS.md`.
- Ingen oppgave er ferdig uten testbevis eller dokumentert blokkering.

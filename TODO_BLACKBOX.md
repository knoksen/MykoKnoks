# TODO_BLACKBOX.md

Prioritert backlog for Blackbox-arbeid på MycoTerrain.

## P0 – Kritisk (må fullføres først)

- [ ] Verifiser at avgrensninger for kontrollerte psykoaktive arter håndheves i data/config/UI
- [ ] Bekreft og dokumenter at `Psilocybe semilanceata` har `forecastEnabled: false`
- [ ] Etabler/forbedre testdekning for sikkerhetskritiske regler
- [ ] Gjennomfør baseline sikkerhetsgjennomgang (kode + avhengigheter) og loggfør funn
- [ ] Oppdater dokumentasjon for dagens demonstrasjonsstatus av habitatmodell

## P1 – Høy prioritet

- [ ] Stabiliser kvalitetspipeline (check/test/lint) for reproduserbar kjøring
- [ ] Reduser kjente tekniske svakheter i `docs/KNOWN_ISSUES.md`
- [ ] Forbedre feilhåndtering og inputvalidering i sentrale flyter
- [ ] Oppdater README med tydelig “hva er demo vs hva er produksjonsklart”

## P2 – Middels prioritet

- [ ] Forbedre utvikleropplevelse (scripts, bedre feilmeldinger, dokumentasjon)
- [ ] Legg til flere akseptansetester iht. `docs/BLACKBOX_ACCEPTANCE_TESTS.md`
- [ ] Stram inn konfigurasjonsstyring og miljøvariabler
- [ ] Forbered struktur for fremtidig backend-integrasjon (uten å implementere full backend)

## P3 – Lavere prioritet / videre arbeid

- [ ] Vurder internasjonalisering (nb/en) designmessig grunnlag
- [ ] Planlegg import/eksport-format (GeoJSON/CSV) på spesifikasjonsnivå
- [ ] Forbered roadmap for offline-kart og synk (design, ikke full implementasjon)
- [ ] Dokumenter forslag til observability/telemetri med personvern som premiss

## Arbeidsregel

- Fullfør høyest prioritet først.
- Hver oppgave skal gi spor i `TODO_PROGRESS.md`.
- Ingen oppgave er “ferdig” uten testbevis eller dokumentert blokkering.

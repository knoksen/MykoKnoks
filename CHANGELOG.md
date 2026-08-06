# CHANGELOG.md

Alle merkbare endringer i prosjektets handoff-dokumentasjon og kjørbare demo loggføres her.

Format inspirert av Keep a Changelog og semver-prinsipper.

## [0.1.2] - 2026-08-06

### Security

- Håndhever at forecast aldri kan aktiveres for `Psilocybe semilanceata`.
- Normaliserer artsnavn før policykontroll for å hindre omgåelse med store bokstaver eller ekstra mellomrom.
- Deaktiverer forecast-kontrollen eksplisitt i UI for den kontrollerte profilen.
- Legger til regresjonstester for app-tilstand, artsskifte og forsøk på policybrudd.

### Changed

- Sentraliserer policylogikk i `src/mycel.js`.
- Gjør presentasjonen fullt lokal ved å erstatte eksternt Unsplash-bilde med innebygd SVG.
- Forbedrer mobil-layout, tastaturfokus og tilgjengelig policytekst.
- Build inkluderer domenemodul og testpakke i `dist`.
- ZIP-pakken er bygget på nytt og verifisert end-to-end.
- Oppdaterer dokumentert baseline til 6/6 tester.

## [0.1.1] - 2026-08-06

### Added

- Blackbox handoff-rammeverk og styringsdokumenter.
- Dokumentasjonspakke i `docs/`.
- Minimal lokal web-app, Node-server og grunnleggende tester.

### Notes

- Første handoff-versjon. Senere gjennomgang avdekket at forecast kunne toggles i UI for kontrollert art; dette er rettet i v0.1.2.

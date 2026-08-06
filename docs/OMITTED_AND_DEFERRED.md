# OMITTED_AND_DEFERRED.md

Full oversikt over hva som bevisst ikke er inkludert i denne handoff-pakken.

## 1) Bygg og distribusjon

Ikke inkludert:

- `package-lock.json`
- `node_modules`
- Generert `android/`-prosjekt og Gradle wrapper
- Windows installer og portable EXE
- Android APK/AAB
- Authenticode-signering
- Android keystore og Play-signering

Årsak:
- Artefakter og signeringsmateriell er miljø- og pipelineavhengig, og inngår ikke i denne kontekstpakken.

## 2) Test og miljøverifisering

Ikke inkludert:

- Fysisk Android-enhetstest
- Ren Windows-maskin sluttverifisering

Årsak:
- Krever dedikert maskinvare/testmiljø utenfor denne leveransen.

## 3) Produksjonsdata og modell

Ikke inkludert:

- Lisensierte soppobservasjoner
- Landdekke, treslag, jord, terreng og hydrologi (produksjonsdatasett)
- Historiske værdata og jordfuktighet i produksjonsløp
- Vitenskapelig trent/validert habitatmodell
- Usikkerhetskart og modellkort
- Produksjonsklar kartleverandør-oppsett

Merknad:
- Dagens habitatlag er en demonstrasjonsmodell, ikke dokumentert sannsynlighetsmodell.

## 4) Backend, konto og personvern

Ikke inkludert:

- Konto/autentisering
- Supabase/PostGIS backend
- Skylagring/synk
- Kryptert lokal lagring
- Telemetry/crash reporting
- Publisert personvernerklæring og vilkår
- SBOM, penetrasjonstest og full sikkerhetsrevisjon

## 5) Produktfunksjoner utsatt

Ikke inkludert:

- Norsk/engelsk språkvelger
- Valgbare søkeresultater
- GeoJSON/CSV eksport/import
- Offlinekart
- Foto-/AI-identifikasjon
- Favoritter, filtre og lagrede steder
- Fellesskap/deling/ekspertverifisering
- Automatiske oppdateringer

## 6) Bevisst sikkerhets-/etikkavgrensning

Følgende er eksplisitt utelatt:

- Presise forekomstkart, hotspots, innsamlingsruter og høstingsprognoser for kontrollerte psykoaktive arter.

Krav som gjelder videre:

- `Psilocybe semilanceata` forblir en ikke-handlingsrettet informasjonsprofil.
- `forecastEnabled: false` skal opprettholdes.

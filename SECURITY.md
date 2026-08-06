# SECURITY.md

## Sikkerhetspolicy for MycoTerrain (handoff-status)

Dette prosjektet er i en engineering handoff-fase. Dokumentet beskriver minimumskrav og rapporteringsrutiner.

## Rapportering av sårbarheter

Inntil dedikert sikkerhetskanal er etablert:

- Rapporter funn privat til prosjektansvarlig via avtalt kanal.
- Ikke publiser proof-of-concept som kan misbrukes.
- Inkluder reproduksjonstrinn, påvirket komponent, alvorlighetsgrad og forslag til tiltak.

## Styrende prinsipper

- Minst mulig innsamling av persondata.
- Ingen hardkodede hemmeligheter.
- Inputvalidering og eksplisitt feilhåndtering.
- Dependency hygiene og regelmessig gjennomgang.

## Domeneavgrensning (kritisk)

Prosjektet skal ikke tilby funksjonalitet som muliggjør misbruk knyttet til kontrollerte psykoaktive arter.

Eksempler på forbudte leveranser:

- Presise forekomstkart/hotspots
- Innsamlingsruter
- Handlingsrettede høstingsprognoser

Spesifikt krav:

- `Psilocybe semilanceata` skal forbli informasjonsprofil med `forecastEnabled: false`.

## Nåværende sikkerhetsstatus

Ikke fullført i denne pakken:

- Full penetrasjonstest
- SBOM
- Full tredjepartsrevisjon
- Produksjonsklar personvern-juridisk pakke

Disse punktene må lukkes før eventuell produksjonssetting.

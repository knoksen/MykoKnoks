# KNOWN_ISSUES.md

Kjente tekniske begrensninger, risikoer og gjeld i nåværende handoff-status.

## 1) Avhengighetslås mangler (`package-lock.json`)

**Status:** Åpen  
**Beskrivelse:** Forsøk på å generere lockfile ble blokkert av miljøets interne npm-proxy (404).  
**Risiko:** Redusert reproduserbarhet av dependency tree mellom miljøer.  
**Tiltak:** Generer lockfile i miljø med tilgang til offentlig npm-registry og commit som kontrollert endring.

## 2) Build-artefakter ikke inkludert

**Status:** Forventet / utsatt  
**Beskrivelse:** Android/Windows build outputs og signeringsartefakter er ikke i repo.  
**Risiko:** Ingen umiddelbar installasjonsklar distribusjon.  
**Tiltak:** Etabler CI/CD for signerte, sporbare releaser.

## 3) Habitatmodell er demonstrasjon, ikke vitenskapelig validert

**Status:** Åpen  
**Beskrivelse:** Nåværende habitatlag representerer demo/logikk, ikke dokumentert sannsynlighetsmodell.  
**Risiko:** Feiltolkning av kvalitet/validitet dersom ikke tydelig kommunisert.  
**Tiltak:** Oppretthold tydelig merking i UI/docs. Ikke fremstille som prediktiv sannhetsmodell.

## 4) Manglende produksjonsdata

**Status:** Åpen  
**Beskrivelse:** Lisensierte observasjoner, terreng-/jord-/hydrologidata m.m. er ikke integrert i produksjonsløp.  
**Risiko:** Begrenset realisme og presisjon i resultater.  
**Tiltak:** Etabler datainntak med lisens/etterlevelse før modelloppgradering.

## 5) Backend og personvernfundament mangler

**Status:** Åpen  
**Beskrivelse:** Ingen kontosystem, synk, publisert personvernpolicy, telemetry-kontroll eller full sikkerhetsrevisjon.  
**Risiko:** Ikke klar for drift med persondata i produksjon.  
**Tiltak:** Implementer minimum personvern- og sikkerhetsrammeverk før skalering.

## 6) Etisk/sikkerhetsmessig avgrensning må håndheves kontinuerlig

**Status:** Kritisk policy  
**Beskrivelse:** Prosjektet skal ikke levere handlingsrettede data for kontrollerte psykoaktive arter.  
**Risiko:** Misbrukspotensial dersom regelverket brytes i kode/data/UI.  
**Tiltak:** Testbar policyhåndheving + eksplisitte kontroller i config, dataflyt og presentasjon.

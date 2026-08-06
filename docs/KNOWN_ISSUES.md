# KNOWN_ISSUES.md

Kjente tekniske begrensninger, risikoer og gjeld i nåværende handoff-status.

## 1) Avhengighetslås mangler (`package-lock.json`)

**Status:** Lav risiko / åpen  
**Beskrivelse:** Prosjektet bruker per v0.1.2 kun Node.js-builtin-funksjonalitet og har ingen eksterne npm-avhengigheter.  
**Risiko:** Begrenset nå, men lockfile må etableres dersom eksterne avhengigheter legges til.  
**Tiltak:** Opprett og commit lockfile samtidig med første eksterne dependency.

## 2) Installerbare produksjonsartefakter mangler

**Status:** Forventet / utsatt  
**Beskrivelse:** APK/AAB og signert Windows-installer er ikke inkludert.  
**Risiko:** Ingen umiddelbar installasjonsklar distribusjon.  
**Tiltak:** Etabler CI/CD for signerte og sporbare releaser.

## 3) Habitatmodell er demonstrasjon, ikke vitenskapelig validert

**Status:** Åpen  
**Beskrivelse:** Nåværende løsning er demo- og handoff-logikk, ikke en dokumentert sannsynlighetsmodell.  
**Risiko:** Feiltolkning dersom status ikke kommuniseres tydelig.  
**Tiltak:** Oppretthold tydelig demo-merking og ikke fremstille modellen som prediktiv sannhet.

## 4) Produksjonsdata mangler

**Status:** Åpen  
**Beskrivelse:** Lisensierte observasjoner og terreng-, jord- og hydrologidata er ikke integrert.  
**Risiko:** Begrenset realisme og presisjon.  
**Tiltak:** Etabler dokumentert datainntak og lisensetterlevelse før modelloppgradering.

## 5) Backend og personvernfundament mangler

**Status:** Åpen  
**Beskrivelse:** Ingen konto, synk, publisert personvernpolicy, telemetrikontroll eller full produksjonssikkerhetsrevisjon.  
**Risiko:** Ikke klar for drift med persondata.  
**Tiltak:** Implementer minimum personvern- og sikkerhetsrammeverk før skalering.

## 6) Etisk/sikkerhetsmessig avgrensning må håndheves kontinuerlig

**Status:** Mitigert i v0.1.2 / kontinuerlig kontroll  
**Beskrivelse:** Forecast-policy håndheves nå i domenelogikk, app-tilstand, UI og seks regresjonstester.  
**Risiko:** Fremtidige features kan introdusere regresjon dersom policyen omgås.  
**Tiltak:** Behold testene som obligatorisk quality gate og krev eksplisitt policygjennomgang ved nye kart-, rute- eller forecast-funksjoner.

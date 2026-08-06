import { enforceForecastPolicy, isControlledSpecies } from './src/mycel.js';

const DEFAULT_SPECIES = 'Psilocybe semilanceata';

const appState = {
  species: DEFAULT_SPECIES,
  forecastEnabled: false,
  notes: []
};

export function createAppState() {
  return {
    ...appState,
    forecastRestricted: isControlledSpecies(appState.species),
    notes: [...appState.notes]
  };
}

export function setSpecies(species) {
  appState.species = species;
  appState.forecastEnabled = enforceForecastPolicy(
    appState.species,
    appState.forecastEnabled
  );
  return appState.species;
}

export function toggleForecast() {
  appState.forecastEnabled = enforceForecastPolicy(
    appState.species,
    !appState.forecastEnabled
  );
  return appState.forecastEnabled;
}

export function isForecastRestricted() {
  return isControlledSpecies(appState.species);
}

export function resetAppState() {
  appState.species = DEFAULT_SPECIES;
  appState.forecastEnabled = false;
  appState.notes = [];
  return createAppState();
}

export function addNote(text) {
  const note = { id: Date.now().toString(), text };
  appState.notes.push(note);
  return note;
}

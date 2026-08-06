const appState = {
  species: 'Psilocybe semilanceata',
  forecastEnabled: false,
  notes: []
};

export function createAppState() {
  return { ...appState, notes: [...appState.notes] };
}

export function setSpecies(species) {
  appState.species = species;
  return appState.species;
}

export function toggleForecast() {
  appState.forecastEnabled = !appState.forecastEnabled;
  return appState.forecastEnabled;
}

export function addNote(text) {
  const note = { id: Date.now().toString(), text };
  appState.notes.push(note);
  return note;
}

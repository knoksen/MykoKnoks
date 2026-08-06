export function formatSpeciesLabel(species) {
  return species.trim().toLowerCase().replace(/\s+/g, ' ');
}

export function getSafetySummary(species, forecastEnabled) {
  return {
    species,
    forecastEnabled,
    safe: species !== 'Psilocybe semilanceata' || !forecastEnabled
  };
}

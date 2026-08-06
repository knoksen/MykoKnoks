const CONTROLLED_SPECIES = new Set([
  'psilocybe semilanceata'
]);

export function formatSpeciesLabel(species) {
  if (typeof species !== 'string') {
    return '';
  }

  return species.trim().toLowerCase().replace(/\s+/g, ' ');
}

export function isControlledSpecies(species) {
  return CONTROLLED_SPECIES.has(formatSpeciesLabel(species));
}

export function enforceForecastPolicy(species, requestedForecastEnabled) {
  return !isControlledSpecies(species) && Boolean(requestedForecastEnabled);
}

export function getSafetySummary(species, requestedForecastEnabled) {
  const controlled = isControlledSpecies(species);
  const forecastEnabled = enforceForecastPolicy(species, requestedForecastEnabled);

  return {
    species,
    controlled,
    requestedForecastEnabled: Boolean(requestedForecastEnabled),
    forecastEnabled,
    policyViolationAttempted: controlled && Boolean(requestedForecastEnabled),
    safe: !controlled || !forecastEnabled
  };
}

import test from 'node:test';
import assert from 'node:assert/strict';
import {
  enforceForecastPolicy,
  formatSpeciesLabel,
  getSafetySummary,
  isControlledSpecies
} from '../src/mycel.js';
import {
  createAppState,
  resetAppState,
  setSpecies,
  toggleForecast
} from '../app.js';

test('formats species labels consistently', () => {
  assert.equal(
    formatSpeciesLabel(' Psilocybe   semilanceata '),
    'psilocybe semilanceata'
  );
});

test('recognizes controlled species independent of case and spacing', () => {
  assert.equal(isControlledSpecies('PSILOCYBE  SEMILANCEATA'), true);
});

test('enforces forecast off for controlled species', () => {
  assert.equal(
    enforceForecastPolicy('Psilocybe semilanceata', true),
    false
  );
});

test('reports an attempted controlled-species policy violation safely', () => {
  const summary = getSafetySummary('Psilocybe semilanceata', true);
  assert.equal(summary.controlled, true);
  assert.equal(summary.forecastEnabled, false);
  assert.equal(summary.policyViolationAttempted, true);
  assert.equal(summary.safe, true);
});

test('app state cannot enable forecast for Psilocybe semilanceata', () => {
  resetAppState();
  assert.equal(toggleForecast(), false);
  assert.equal(createAppState().forecastEnabled, false);
});

test('switching to a controlled species immediately clears forecast state', () => {
  resetAppState();
  setSpecies('Amanita muscaria');
  assert.equal(toggleForecast(), true);
  setSpecies('Psilocybe semilanceata');
  assert.equal(createAppState().forecastEnabled, false);
});

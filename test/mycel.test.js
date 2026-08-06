import test from 'node:test';
import assert from 'node:assert/strict';
import { formatSpeciesLabel, getSafetySummary } from '../src/mycel.js';

test('formats species labels consistently', () => {
  assert.equal(formatSpeciesLabel(' Psilocybe semilanceata '), 'psilocybe semilanceata');
});

test('disables forecast for controlled species', () => {
  const summary = getSafetySummary('Psilocybe semilanceata', true);
  assert.equal(summary.safe, false);
});

test('keeps the app safe when forecast is off', () => {
  const summary = getSafetySummary('Psilocybe semilanceata', false);
  assert.equal(summary.safe, true);
});

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const outDir = path.join(__dirname, 'dist');
mkdirSync(outDir, { recursive: true });

const files = ['index.html', 'styles.css', 'app.js', 'server.js', 'package.json'];
for (const file of files) {
  const source = path.join(__dirname, file);
  const target = path.join(outDir, file);
  const content = readFileSync(source, 'utf8');
  writeFileSync(target, content);
}

const manifest = {
  name: 'MycoTerrain',
  version: '0.1.1',
  createdAt: new Date().toISOString(),
  checks: ['npm test', 'npm run check']
};
writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));

console.log(`Built distribution bundle at ${outDir}`);

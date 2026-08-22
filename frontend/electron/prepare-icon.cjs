const fs = require('node:fs')
const path = require('node:path')

const source = path.join(__dirname, 'icon.ico.b64')
const buildDir = path.join(__dirname, '..', 'build')
const target = path.join(buildDir, 'icon.ico')

const encoded = fs.readFileSync(source, 'utf8').trim()
if (!encoded) throw new Error('Desktop icon source is empty')

const bytes = Buffer.from(encoded, 'base64')
if (bytes.length < 22 || bytes.readUInt16LE(0) !== 0 || bytes.readUInt16LE(2) !== 1) {
  throw new Error('Desktop icon source is not a valid ICO file')
}

fs.mkdirSync(buildDir, { recursive: true })
fs.writeFileSync(target, bytes)
console.log(`Prepared Windows icon: ${target} (${bytes.length} bytes)`)

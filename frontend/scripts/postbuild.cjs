const fs = require('fs')
const path = require('path')

const indexPath = path.resolve(__dirname, '../dist/index.html')
if (!fs.existsSync(indexPath)) {
  console.log('dist/index.html not found, skipping')
  process.exit(0)
}

let html = fs.readFileSync(indexPath, 'utf8')
const before = html
html = html.replace(/<script type="module" crossorigin>/g, '<script type="module">')

if (html !== before) {
  fs.writeFileSync(indexPath, html)
  console.log('Removed crossorigin from inline module script')
} else {
  console.log('No inline module script with crossorigin found')
}

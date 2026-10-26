"""Read-only deployment acceptance checks; no imports, writes or predictions."""
import argparse
import json
import re
from urllib.request import urlopen
from urllib.parse import urljoin, urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='https://mykoknoks.jarlhalla.com')
args = parser.parse_args()
base = args.base.rstrip('/')

def fetch(path):
    with urlopen(base + path, timeout=20) as response:
        return response.read().decode(), response.headers.get('Content-Type', '')

landing, _ = fetch('/')
assert 'MykoKnoks' in landing, 'Existing landing page missing'
html, mime = fetch('/app/')
assert 'text/html' in mime, mime
assets = re.findall(r'(?:src|href)=["\']([^"\']+\.(?:js|css))["\']', html)
assert assets, 'No built JS/CSS assets'
for asset in assets:
    absolute = urljoin(base + '/app/', asset)
    assert urlsplit(absolute).netloc == urlsplit(base).netloc, absolute
    path = urlsplit(absolute).path
    body, kind = fetch(path)
    assert body and 'text/html' not in kind, f'Asset returned HTML: {path}'
body, mime = fetch('/mykoknoks-api/health')
assert 'json' in mime, 'Health route returned HTML instead of JSON'
health = json.loads(body)
assert health['status'] == 'ok' and health['service'] == 'MykoKnoks', health
assert health['root_path'] == '/mykoknoks-api', health
print('PASS: landing, app, JS/CSS assets and API health')
print('NOT RUN: browser/WebGL, live data, store population and scientific calibration')

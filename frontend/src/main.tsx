import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('MykoKnoks root element is missing')

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

document.getElementById('boot-fallback')?.remove()

const isAndroidAssetHost = window.location.hostname === 'appassets.androidplatform.net'
if ('serviceWorker' in navigator && import.meta.env.PROD && !isAndroidAssetHost) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('./sw.js')
  })
}

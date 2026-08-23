import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './advanced.css'
import './temporal.css'
import './version.css'
import './map-pro.css'
import './eco-gis.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('MykoKnoks root element is missing')

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

document.getElementById('boot-fallback')?.remove()

const isAndroidAssetHost = window.location.hostname === 'appassets.androidplatform.net'
const isDesktopRuntime = Boolean(window.mykoDesktop?.isDesktop)
document.documentElement.classList.toggle('desktop-runtime', isDesktopRuntime)

if ('serviceWorker' in navigator && import.meta.env.PROD && !isAndroidAssetHost && !isDesktopRuntime) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('./sw.js')
  })
}

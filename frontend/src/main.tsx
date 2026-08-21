import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

const isAndroidAssetHost = window.location.hostname === 'appassets.androidplatform.net'
if ('serviceWorker' in navigator && import.meta.env.PROD && !isAndroidAssetHost) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('./sw.js')
  })
}

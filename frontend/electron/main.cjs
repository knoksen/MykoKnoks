const { app, BrowserWindow, Menu, dialog, ipcMain, session, shell } = require('electron')
const fs = require('node:fs')
const path = require('node:path')

const APP_NAME = 'MykoKnoks'
const DEFAULT_WIDTH = 1500
const DEFAULT_HEIGHT = 980
const HTTP_TIMEOUT_MS = 20000
let mainWindow = null

function statePath() {
  return path.join(app.getPath('userData'), 'window-state.json')
}

function loadWindowState() {
  try {
    const parsed = JSON.parse(fs.readFileSync(statePath(), 'utf8'))
    if (Number.isFinite(parsed.width) && Number.isFinite(parsed.height)) return parsed
  } catch {
    // First launch or invalid state: use safe defaults.
  }
  return { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT }
}

function saveWindowState(win) {
  if (!win || win.isDestroyed()) return
  try {
    const bounds = win.isMaximized() ? win.getNormalBounds() : win.getBounds()
    fs.mkdirSync(app.getPath('userData'), { recursive: true })
    fs.writeFileSync(statePath(), JSON.stringify(bounds, null, 2), 'utf8')
  } catch {
    // Window persistence must never block shutdown.
  }
}

async function savePdf(win) {
  if (!win || win.isDestroyed()) return { ok: false, reason: 'window-unavailable' }
  const target = await dialog.showSaveDialog(win, {
    title: 'Export MykoKnoks report as PDF',
    defaultPath: `MykoKnoks-${new Date().toISOString().slice(0, 10)}.pdf`,
    filters: [{ name: 'PDF', extensions: ['pdf'] }],
  })
  if (target.canceled || !target.filePath) return { ok: false, canceled: true }
  const pdf = await win.webContents.printToPDF({ printBackground: true, pageSize: 'A4' })
  await fs.promises.writeFile(target.filePath, pdf)
  return { ok: true, path: target.filePath }
}

async function saveScreenshot(win) {
  if (!win || win.isDestroyed()) return { ok: false, reason: 'window-unavailable' }
  const target = await dialog.showSaveDialog(win, {
    title: 'Save MykoKnoks map screenshot',
    defaultPath: `MykoKnoks-${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
    filters: [{ name: 'PNG image', extensions: ['png'] }],
  })
  if (target.canceled || !target.filePath) return { ok: false, canceled: true }
  const image = await win.webContents.capturePage()
  await fs.promises.writeFile(target.filePath, image.toPNG())
  return { ok: true, path: target.filePath }
}

async function desktopHttpRequest(url, options = {}) {
  let parsed
  try {
    parsed = new URL(url)
  } catch {
    throw new Error('Invalid API URL')
  }
  if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('Only HTTP(S) API requests are allowed')

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), HTTP_TIMEOUT_MS)
  try {
    const response = await fetch(parsed.toString(), {
      method: options.method || 'GET',
      headers: options.headers || {},
      body: typeof options.body === 'string' ? options.body : undefined,
      signal: controller.signal,
    })
    return {
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      body: await response.text(),
      contentType: response.headers.get('content-type') || '',
    }
  } catch (error) {
    if (error && error.name === 'AbortError') throw new Error(`API request timed out after ${HTTP_TIMEOUT_MS / 1000}s`)
    throw error
  } finally {
    clearTimeout(timer)
  }
}

function buildMenu(win) {
  return Menu.buildFromTemplate([
    {
      label: 'File',
      submenu: [
        { label: 'Export PDF…', accelerator: 'Ctrl+Shift+P', click: () => void savePdf(win) },
        { label: 'Save screenshot…', accelerator: 'Ctrl+Shift+S', click: () => void saveScreenshot(win) },
        { type: 'separator' },
        { role: 'quit', label: 'Exit MykoKnoks' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'MykoKnoks API health',
          click: () => void shell.openExternal('https://knoksen.nova.usbx.me/mykoknoks-api/health'),
        },
        {
          label: 'Project repository',
          click: () => void shell.openExternal('https://github.com/knoksen/MykoKnoks'),
        },
      ],
    },
  ])
}

function createWindow() {
  const state = loadWindowState()
  const win = new BrowserWindow({
    title: APP_NAME,
    width: state.width || DEFAULT_WIDTH,
    height: state.height || DEFAULT_HEIGHT,
    x: Number.isFinite(state.x) ? state.x : undefined,
    y: Number.isFinite(state.y) ? state.y : undefined,
    minWidth: 1050,
    minHeight: 720,
    backgroundColor: '#0b1210',
    show: false,
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  })

  mainWindow = win
  Menu.setApplicationMenu(buildMenu(win))

  win.once('ready-to-show', () => win.show())
  win.on('close', () => saveWindowState(win))
  win.on('closed', () => {
    if (mainWindow === win) mainWindow = null
  })

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) void shell.openExternal(url)
    return { action: 'deny' }
  })

  win.webContents.on('will-navigate', (event, url) => {
    const current = win.webContents.getURL()
    try {
      if (new URL(url).origin === new URL(current).origin) return
    } catch {
      // Treat malformed/opaque navigations as external.
    }
    event.preventDefault()
    if (/^https?:\/\//i.test(url)) void shell.openExternal(url)
  })

  const devServerUrl = process.env.MYKOKNOKS_DEV_SERVER_URL
  if (devServerUrl) void win.loadURL(devServerUrl)
  else void win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))

  return win
}

const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show()
    mainWindow.focus()
  })

  app.whenReady().then(() => {
    app.setAppUserModelId('no.jarlhalla.mykoknoks')

    session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
      callback(permission === 'geolocation')
    })

    ipcMain.handle('desktop:runtime-info', () => ({
      appName: app.getName(),
      version: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
      electron: process.versions.electron,
      chrome: process.versions.chrome,
    }))
    ipcMain.handle('desktop:save-pdf', () => savePdf(mainWindow))
    ipcMain.handle('desktop:save-screenshot', () => saveScreenshot(mainWindow))
    ipcMain.handle('desktop:http-request', (_event, url, options) => desktopHttpRequest(url, options))
    ipcMain.handle('desktop:open-external', (_event, url) => {
      if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) return false
      void shell.openExternal(url)
      return true
    })

    createWindow()

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

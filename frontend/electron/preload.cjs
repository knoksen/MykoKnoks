const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('mykoDesktop', {
  isDesktop: true,
  getRuntimeInfo: () => ipcRenderer.invoke('desktop:runtime-info'),
  savePdf: () => ipcRenderer.invoke('desktop:save-pdf'),
  saveScreenshot: () => ipcRenderer.invoke('desktop:save-screenshot'),
  openExternal: url => ipcRenderer.invoke('desktop:open-external', url),
})

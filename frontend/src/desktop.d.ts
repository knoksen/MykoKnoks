export {}

declare global {
  interface Window {
    mykoDesktop?: {
      isDesktop: boolean
      getRuntimeInfo: () => Promise<{
        appName: string
        version: string
        platform: string
        arch: string
        electron: string
        chrome: string
      }>
      savePdf: () => Promise<{ ok: boolean; canceled?: boolean; path?: string; reason?: string }>
      saveScreenshot: () => Promise<{ ok: boolean; canceled?: boolean; path?: string; reason?: string }>
      openExternal: (url: string) => Promise<boolean>
    }
  }
}

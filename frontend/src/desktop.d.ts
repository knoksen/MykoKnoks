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
      httpRequest: (
        url: string,
        options?: { method?: string; headers?: Record<string, string>; body?: string },
      ) => Promise<{
        ok: boolean
        status: number
        statusText: string
        body: string
        contentType: string
      }>
      openExternal: (url: string) => Promise<boolean>
    }
  }
}

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The IDE proxy host comes from VSCODE_PROXY_URI (e.g. https://<id>.cloudfront.net/proxy/{{port}}/),
// so no workshop hostname is committed. Vite allows any *.cloudfront.net host, as the lab guide
// recommends (never `allowedHosts: true`).
const PROXY_HOST = (() => {
  try {
    return new URL((process.env.VSCODE_PROXY_URI ?? '').replace('{{port}}', '5173')).hostname
  } catch {
    return undefined
  }
})()

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Dev only: the IDE proxy serves this app under /absproxy/5173/ (prefix is
  // not stripped), so asset URLs must include it. Build output stays at '/'.
  base: command === 'serve' ? '/absproxy/5173/' : '/',
  server: {
    port: 5173,
    strictPort: true,
    allowedHosts: ['.cloudfront.net'],
    // HMR websocket goes through CloudFront over HTTPS on 443 (local defaults when no proxy).
    hmr: PROXY_HOST ? { protocol: 'wss', host: PROXY_HOST, clientPort: 443 } : undefined,
    // Royal Table (Account Growth Agent) (Streamlit on 8501, started with
    // --server.baseUrlPath=absproxy/5173/curator) is served through this same
    // dev server, so everything is reachable on port 5173.
    proxy: {
      '/absproxy/5173/curator': {
        target: 'http://127.0.0.1:8501',
        ws: true,
      },
    },
  },
}))

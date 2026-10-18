import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base '/admin/'：build 出嚟嘅 asset URL 會係 /admin/assets/…，
// 配合 Spring Boot 將 dist 擺去 static/admin/ 同 AdminForwardController。
export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  build: {
    outDir: 'dist',
  },
})

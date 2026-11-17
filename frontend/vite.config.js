import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Puerto propio para convivir con la web de Spring (5173); si está ocupado, falla en vez de moverse a otro
  server: { port: 5174, strictPort: true },
})

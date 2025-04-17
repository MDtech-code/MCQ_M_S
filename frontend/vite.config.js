import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  

  server: {
    host:true,
    hmr: {
      clientPort: 5173  // Explicit port for HMR
    },
    watch: {
      usePolling: true  // Enable file system polling
    },
    proxy: {
      'api/': {
        target: 'http://localhost:8000', // to run on local
        //target: 'https://backend:8000',  // to run on docker
        changeOrigin: true,
        secure: false,
        
      }
    }
  }

})

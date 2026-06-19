/// <reference types="vite/client" />

// Configuração injetada em runtime pelo container (public/config.js ->
// sobrescrito por docker-entrypoint.d/40-app-config.sh a partir de VITE_API_URL).
interface Window {
  __APP_CONFIG__?: {
    API_URL?: string;
  };
}

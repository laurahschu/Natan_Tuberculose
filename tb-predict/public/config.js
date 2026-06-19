// Configuração de runtime. Em produção (Docker), este arquivo é sobrescrito
// pelo container a partir da env VITE_API_URL. Em desenvolvimento, mantém o
// objeto vazio e a aplicação usa o fallback de import.meta.env / localhost.
window.__APP_CONFIG__ = window.__APP_CONFIG__ || {};

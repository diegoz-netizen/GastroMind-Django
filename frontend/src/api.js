import axios from 'axios'

// Lab 12, Ejercicio 3: una sola instancia de Axios para la Parte 1 (src/practica).
// La dirección del servidor está solo aquí: si Django cambia de puerto o de dominio, se cambia en un lugar.
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 8000,
})

// La API de Django pide el JWT que emite Spring: se toma de la sesión iniciada en el panel
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('gastromind_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api

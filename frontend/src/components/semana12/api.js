import axios from 'axios'

// Django (8000) entrega el catálogo y los reportes; Spring (8080) hace el login, el personal, las mesas y los pedidos.
// Django no tiene login: valida el mismo token que emite Spring.
const URL_SPRING = 'http://localhost:8080/api'
const CLAVE_TOKEN = 'gastromind_token'
const CLAVE_USUARIO = 'gastromind_usuario'

function crearCliente(baseURL) {
  const cliente = axios.create({ baseURL, timeout: 8000 })
  // Cada petición lleva el token en la cabecera Authorization
  cliente.interceptors.request.use((config) => {
    const token = sessionStorage.getItem(CLAVE_TOKEN)
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  // Un 401 es token vencido o ausente: se cierra la sesión y se vuelve al inicio de sesión
  cliente.interceptors.response.use(
    (respuesta) => respuesta,
    (error) => {
      if (error.response?.status === 401) sesion.cerrar()
      return Promise.reject(error)
    },
  )
  return cliente
}

const api = crearCliente('http://127.0.0.1:8000/api/catalogo')
export const apiSpring = crearCliente(URL_SPRING)

export const sesion = {
  token: () => sessionStorage.getItem(CLAVE_TOKEN),
  usuario: () => {
    try {
      return JSON.parse(sessionStorage.getItem(CLAVE_USUARIO))
    } catch {
      return null
    }
  },
  cerrar: () => {
    sessionStorage.removeItem(CLAVE_TOKEN)
    sessionStorage.removeItem(CLAVE_USUARIO)
    window.dispatchEvent(new Event('sesion-cambio'))
  },
}

// Login contra Spring: el token y el nombre quedan solo en sessionStorage (nada de claves en el código)
export async function iniciarSesion(correo, password) {
  const { data } = await axios.post(`${URL_SPRING}/auth/login`, { correo, password }, { timeout: 8000 })
  sessionStorage.setItem(CLAVE_TOKEN, data.token)
  sessionStorage.setItem(CLAVE_USUARIO, JSON.stringify({ nombre: data.nombreCompleto, rol: data.rol }))
  window.dispatchEvent(new Event('sesion-cambio'))
  return data
}

export default api

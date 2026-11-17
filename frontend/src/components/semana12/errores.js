// La API responde { error, mensaje, campos? } (HL-014). Estas funciones lo convierten en texto para la pantalla.
export function mensajesDeError(err) {
  if (!err.response) return ['No hay conexión con el servidor.']
  const datos = err.response.data ?? {}
  if (datos.campos) return Object.values(datos.campos).map(String)
  return [datos.mensaje ?? datos.message ?? `Error ${err.response.status}`]
}

// Errores por campo: { nombre: 'Este campo no puede estar en blanco.' }
export function camposDeError(err) {
  const campos = err.response?.data?.campos
  return campos && typeof campos === 'object' ? campos : {}
}

// Mensaje general cuando el error no es de un campo concreto
export function mensajeGeneral(err) {
  if (err.response?.data?.campos) return ''
  return mensajesDeError(err)[0]
}

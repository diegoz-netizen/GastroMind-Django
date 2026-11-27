import { useEffect, useState } from 'react'
import api from '../api'

// Lab 12, Parte 1: Ajax con un recurso simple de la API de la Semana 8, las categorías de la carta.
// GET    /api/catalogo/categorias/?search=   listar y buscar (200)
// POST   /api/catalogo/categorias/           crear (201; 400 si el nombre está vacío o repetido: validate_nombre)
// PATCH  /api/catalogo/categorias/{id}/      renombrar (200)
// DELETE /api/catalogo/categorias/{id}/      eliminar (204; 409 si tiene platillos)
const URL = '/catalogo/categorias/'

// El error de la API llega como { error, mensaje, campos? }: se muestra el texto que envía el serializer
function textoDeError(err) {
  if (!err.response) return 'No hay conexión con el servidor.'
  const datos = err.response.data
  if (datos?.campos) return Object.values(datos.campos).flat().join(' ')
  return datos?.mensaje ?? `Error ${err.response.status}`
}

function ListaPractica() {
  const [registros, setRegistros] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [buscar, setBuscar] = useState('')
  const [nombre, setNombre] = useState('')
  const [errorForm, setErrorForm] = useState('')
  const [editando, setEditando] = useState(null)
  const [nombreEditado, setNombreEditado] = useState('')
  const [mensaje, setMensaje] = useState(null) // { texto, error }

  // Ejercicios 4, 5 y 8: GET al montar y cada vez que cambia el texto de búsqueda.
  // La función del efecto no es async (debe devolver nada o la limpieza): la petición va en una función interna.
  useEffect(() => {
    const controlador = new AbortController()
    async function cargar() {
      setCargando(true)
      setError('')
      try {
        const respuesta = await api.get(URL, { params: { search: buscar }, signal: controlador.signal })
        setRegistros(respuesta.data)
      } catch (err) {
        if (err.code === 'ERR_CANCELED') return // la cancelamos nosotros: llegó una búsqueda más nueva
        console.error('No se pudo cargar la lista:', err.message)
        setError('No se pudo cargar la lista.')
      } finally {
        // Si se canceló, la petición nueva sigue cargando: no se apaga el "Cargando..."
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    // Limpieza: si el texto cambia antes de que llegue la respuesta, se cancela la petición anterior
    return () => controlador.abort()
  }, [buscar])

  // Ejercicio 6: POST con un formulario controlado (201, o 400 con el mensaje del serializer)
  async function crear(evento) {
    evento.preventDefault()
    setErrorForm('')
    setMensaje(null)
    try {
      const respuesta = await api.post(URL, { nombre })
      setRegistros([...registros, respuesta.data])
      setNombre('')
      setMensaje({ texto: `Se creó «${respuesta.data.nombre}».` })
    } catch (err) {
      setErrorForm(textoDeError(err))
    }
  }

  // Ejercicio 7: PATCH (200) y actualización con map()
  async function guardarNombre(id) {
    setErrorForm('')
    setMensaje(null)
    try {
      const respuesta = await api.patch(`${URL}${id}/`, { nombre: nombreEditado })
      setRegistros(registros.map((r) => (r.id === id ? respuesta.data : r)))
      setEditando(null)
      setMensaje({ texto: `Ahora se llama «${respuesta.data.nombre}».` })
    } catch (err) {
      setMensaje({ texto: textoDeError(err), error: true })
    }
  }

  // Ejercicio 7: DELETE (204) y actualización con filter()
  async function eliminar(registro) {
    if (!window.confirm(`¿Eliminar la categoría «${registro.nombre}»?`)) return
    setErrorForm('')
    setMensaje(null)
    try {
      await api.delete(`${URL}${registro.id}/`)
      setRegistros(registros.filter((r) => r.id !== registro.id))
      setMensaje({ texto: `Se eliminó «${registro.nombre}».` })
    } catch (err) {
      setMensaje({ texto: textoDeError(err), error: true }) // 409: la categoría tiene platillos
    }
  }

  return (
    <section className="content-card practica-lab12">
      <h2>Práctica Lab 12: categorías con Ajax</h2>
      <p className="field-help">Recurso simple de la API: <code>/api/catalogo/categorias/</code></p>

      <form onSubmit={crear} className="practica-form" noValidate>
        <input value={nombre} onChange={(e) => { setNombre(e.target.value); setErrorForm('') }} placeholder="Nueva categoría" maxLength={100} />
        <button type="submit">Crear</button>
      </form>
      {errorForm && <p className="practica-error">{errorForm}</p>}

      <input
        className="practica-buscar"
        value={buscar}
        onChange={(e) => setBuscar(e.target.value)}
        placeholder="Buscar categoría…"
      />
      {mensaje && <p className={mensaje.error ? 'practica-error' : 'practica-mensaje'}>{mensaje.texto}</p>}

      {cargando && <p>Cargando...</p>}
      {!cargando && error && <p className="practica-error">{error}</p>}
      {!cargando && !error && registros.length === 0 && <p>No hay categorías.</p>}
      {!cargando && !error && registros.length > 0 && (
        <ul className="practica-lista">
          {registros.map((registro) => (
            <li key={registro.id}>
              {editando === registro.id ? (
                <>
                  <input value={nombreEditado} onChange={(e) => setNombreEditado(e.target.value)} />
                  <button type="button" onClick={() => guardarNombre(registro.id)}>Guardar</button>
                  <button type="button" onClick={() => setEditando(null)}>Cancelar</button>
                </>
              ) : (
                <>
                  <span>{registro.nombre}</span>
                  <button type="button" onClick={() => { setEditando(registro.id); setNombreEditado(registro.nombre) }}>Editar</button>
                  <button type="button" onClick={() => eliminar(registro)}>Eliminar</button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default ListaPractica

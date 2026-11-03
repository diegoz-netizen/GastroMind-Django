import { useState } from 'react'
import EmpleadoCard from './EmpleadoCard'

const ROLES = ['MOZO', 'COCINERO', 'ALMACENERO', 'ADMINISTRADOR']
const FORM_VACIO = { nombreCompleto: '', correo: '', rol: 'MOZO', restauranteId: '1' }
const CORREO_VALIDO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Personal con buscador (nombre o correo) y formulario de registro (HU-01).
// La lista vive en el estado: falta enviar a POST /api/empleados de Spring para guardarlo.
function ListaEmpleados({ empleados, restaurantes }) {
  const [lista, setLista] = useState(empleados)
  const [busqueda, setBusqueda] = useState('')
  const [form, setForm] = useState(FORM_VACIO)
  const [error, setError] = useState('')

  const texto = busqueda.trim().toLowerCase()
  const visibles = lista.filter(
    (empleado) => empleado.nombreCompleto.toLowerCase().includes(texto) || empleado.correo.toLowerCase().includes(texto),
  )

  function cambiarCampo(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function registrar(e) {
    e.preventDefault()
    const nombreCompleto = form.nombreCompleto.trim()
    const correo = form.correo.trim().toLowerCase()
    // Mismas reglas que el registro de empleados (HU-01): datos obligatorios, correo válido y único
    if (!nombreCompleto) {
      setError('El nombre completo es obligatorio.')
      return
    }
    if (!CORREO_VALIDO.test(correo)) {
      setError('Ingrese un correo válido.')
      return
    }
    if (lista.some((empleado) => empleado.correo.toLowerCase() === correo)) {
      setError('Ya existe un empleado con ese correo.')
      return
    }
    const nuevo = {
      id: Math.max(0, ...lista.map((empleado) => empleado.id)) + 1,
      nombreCompleto,
      rol: form.rol,
      estado: 'ACTIVO',
      correo,
      restauranteId: Number(form.restauranteId),
    }
    setLista([...lista, nuevo])
    setForm(FORM_VACIO)
    setError('')
  }

  return (
    <>
      <input
        className="buscador"
        type="search"
        placeholder="Buscar por nombre o correo"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />
      {lista.length === 0 ? (
        <p className="vacio">No hay registros</p>
      ) : visibles.length === 0 ? (
        <p className="vacio">Ningún empleado coincide con «{busqueda}»</p>
      ) : (
        <ul className="lista">
          {visibles.map((empleado) => (
            <EmpleadoCard
              key={empleado.id}
              nombreCompleto={empleado.nombreCompleto}
              rol={empleado.rol}
              estadoInicial={empleado.estado}
              correo={empleado.correo}
            />
          ))}
        </ul>
      )}

      <form className="formulario" onSubmit={registrar} noValidate>
        <h3>Registrar empleado</h3>
        <label>
          Nombre completo
          <input name="nombreCompleto" value={form.nombreCompleto} onChange={cambiarCampo} maxLength={150} />
        </label>
        <label>
          Correo
          <input name="correo" type="email" value={form.correo} onChange={cambiarCampo} />
        </label>
        <label>
          Rol
          <select name="rol" value={form.rol} onChange={cambiarCampo}>
            {ROLES.map((rol) => (
              <option key={rol} value={rol}>
                {rol}
              </option>
            ))}
          </select>
        </label>
        <label>
          Restaurante
          <select name="restauranteId" value={form.restauranteId} onChange={cambiarCampo}>
            {restaurantes.map((restaurante) => (
              <option key={restaurante.id} value={restaurante.id}>
                {restaurante.nombre}
              </option>
            ))}
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Registrar</button>
      </form>
    </>
  )
}

export default ListaEmpleados

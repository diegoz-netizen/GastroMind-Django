import { useState } from 'react'
import InsumoCard from './InsumoCard'

const UNIDADES = ['g', 'kg', 'ml', 'l', 'unidades']
const FORM_VACIO = { nombre: '', unidad_medida: 'kg', costo_unitario: '', stock_minimo: '' }

// Lista de insumos con buscador y formulario. La lista vive en el estado de este componente:
// lo que se agrega todavía no se guarda en Django (falta llamar a POST /api/catalogo/insumos/, Semana 12).
function ListaInsumos({ insumos }) {
  const [lista, setLista] = useState(insumos)
  const [busqueda, setBusqueda] = useState('')
  const [form, setForm] = useState(FORM_VACIO)
  const [error, setError] = useState('')

  const visibles = lista.filter((insumo) => insumo.nombre.toLowerCase().includes(busqueda.trim().toLowerCase()))

  function cambiarCampo(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function agregar(e) {
    e.preventDefault()
    const nombre = form.nombre.trim()
    // Mismas reglas que IngredienteSerializer (HU-05, CA-05)
    if (!nombre) {
      setError('El nombre es obligatorio.')
      return
    }
    if (lista.some((insumo) => insumo.nombre.toLowerCase() === nombre.toLowerCase())) {
      setError('Ya existe un insumo con ese nombre en el restaurante.')
      return
    }
    if (!(Number(form.costo_unitario) > 0) || !(Number(form.stock_minimo) > 0)) {
      setError('El costo unitario y el stock mínimo deben ser mayores que 0.')
      return
    }
    const nuevo = {
      id: Math.max(0, ...lista.map((insumo) => insumo.id)) + 1,
      nombre,
      unidad_medida: form.unidad_medida,
      costo_unitario: Number(form.costo_unitario).toFixed(2),
      stock_actual: '0.00', // como en la API: un insumo nace con stock 0 (solo sube con una compra, HU-14)
      stock_minimo: Number(form.stock_minimo).toFixed(2),
      tipo_control: 'RECETA',
      bajo_stock_minimo: true,
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
        placeholder="Buscar insumo por nombre"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />
      {lista.length === 0 ? (
        <p className="vacio">No hay registros</p>
      ) : visibles.length === 0 ? (
        <p className="vacio">Ningún insumo coincide con «{busqueda}»</p>
      ) : (
        <ul className="lista">
          {visibles.map((insumo) => (
            <InsumoCard
              key={insumo.id}
              nombre={insumo.nombre}
              unidad={insumo.unidad_medida}
              costo={insumo.costo_unitario}
              stock={insumo.stock_actual}
              bajoMinimo={insumo.bajo_stock_minimo}
            />
          ))}
        </ul>
      )}

      <form className="formulario" onSubmit={agregar} noValidate>
        <h3>Nuevo insumo</h3>
        <label>
          Nombre
          <input name="nombre" value={form.nombre} onChange={cambiarCampo} maxLength={150} />
        </label>
        <label>
          Unidad
          <select name="unidad_medida" value={form.unidad_medida} onChange={cambiarCampo}>
            {UNIDADES.map((unidad) => (
              <option key={unidad} value={unidad}>
                {unidad}
              </option>
            ))}
          </select>
        </label>
        <label>
          Costo unitario (S/)
          <input name="costo_unitario" type="number" step="0.01" value={form.costo_unitario} onChange={cambiarCampo} />
        </label>
        <label>
          Stock mínimo
          <input name="stock_minimo" type="number" step="0.001" value={form.stock_minimo} onChange={cambiarCampo} />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Agregar insumo</button>
      </form>
    </>
  )
}

export default ListaInsumos

import { useState } from 'react'

const UNIDADES = ['g', 'kg', 'ml', 'l', 'unidades']
const FORM_VACIO = { nombre: '', unidad_medida: 'kg', costo_unitario: '', stock_minimo: '' }

// Lab 10: este formulario estaba dentro de ListaInsumos y agregaba a su propia lista.
// Lab 11: es un hijo controlado. Valida como IngredienteSerializer (HU-05) y entrega el insumo al padre con onGuardar.
function FormularioInsumo({ nombresUsados, onGuardar }) {
  const [form, setForm] = useState(FORM_VACIO)
  const [error, setError] = useState('')

  function cambiarCampo(evento) {
    setForm({ ...form, [evento.target.name]: evento.target.value })
  }

  function enviar(evento) {
    evento.preventDefault()
    const nombre = form.nombre.trim()
    // Mismas reglas que IngredienteSerializer (HU-05, CA-05)
    if (!nombre) {
      setError('El nombre es obligatorio.')
      return
    }
    if (nombresUsados.includes(nombre.toLowerCase())) {
      setError('Ya existe un insumo con ese nombre en el restaurante.')
      return
    }
    if (!(Number(form.costo_unitario) >= 0.01) || !(Number(form.stock_minimo) >= 0.001)) {
      setError('El costo unitario y el stock mínimo deben ser mayores que 0.')
      return
    }
    onGuardar({
      nombre,
      unidad_medida: form.unidad_medida,
      costo_unitario: Number(form.costo_unitario).toFixed(2),
      stock_actual: '0.00', // como en la API: un insumo nace con stock 0 (solo sube con una compra, HU-14)
      stock_minimo: Number(form.stock_minimo).toFixed(2),
      tipo_control: 'RECETA',
      bajo_stock_minimo: true,
    })
    setForm(FORM_VACIO)
    setError('')
  }

  return (
    <form className="formulario" onSubmit={enviar} noValidate>
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
  )
}

export default FormularioInsumo

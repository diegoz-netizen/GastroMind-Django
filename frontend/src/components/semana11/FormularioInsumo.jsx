import { useState } from 'react'
import { Button, Field, Panel } from '../../ui'

const UNIDADES = ['g', 'kg', 'ml', 'l', 'unidades']
const FORM_VACIO = { nombre: '', unidad_medida: '', costo_unitario: '', stock_minimo: '' }

// Lab 10: este formulario estaba dentro de ListaInsumos y agregaba a su propia lista.
// Lab 11: es un hijo controlado: valida y entrega los datos al padre con onGuardar.
// Lab 12: onGuardar hace el POST. Si la API responde 400, el padre devuelve `errores` por campo y un `general`.
function FormularioInsumo({ nombresUsados, onGuardar, errores = {}, general = '' }) {
  const [form, setForm] = useState(FORM_VACIO)
  const [error, setError] = useState('')

  function cambiarCampo(evento) {
    setForm({ ...form, [evento.target.name]: evento.target.value })
  }

  async function enviar(evento) {
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
    setError('')
    // El padre responde true si la API aceptó el insumo (201): solo entonces se limpia el formulario
    const guardado = await onGuardar({
      nombre,
      unidad_medida: form.unidad_medida,
      costo_unitario: form.costo_unitario,
      stock_minimo: form.stock_minimo,
    })
    if (guardado) setForm(FORM_VACIO)
  }

  return (
    <Panel title="Nuevo insumo" subtitle="Registra un producto en el almacén.">
      <form onSubmit={enviar} noValidate>
        <Field label="Nombre del insumo" error={errores.nombre}>
          <input name="nombre" value={form.nombre} onChange={cambiarCampo} placeholder="Ej. Harina sin preparar" maxLength={150} />
        </Field>
        <div className="field-grid">
          <Field label="Costo unitario" error={errores.costo_unitario}>
            <div className="input-prefix">
              <span>S/</span>
              <input name="costo_unitario" type="number" step="0.01" value={form.costo_unitario} onChange={cambiarCampo} placeholder="0.00" />
            </div>
          </Field>
          <Field label="Unidad" error={errores.unidad_medida}>
            <select name="unidad_medida" value={form.unidad_medida} onChange={cambiarCampo}>
              <option value="" disabled>Elegir</option>
              {UNIDADES.map((unidad) => <option key={unidad} value={unidad}>{unidad}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Stock mínimo" help="El stock inicial es 0: sube al registrar compras." error={errores.stock_minimo}>
          <input name="stock_minimo" type="number" step="0.001" value={form.stock_minimo} onChange={cambiarCampo} placeholder="0" />
        </Field>
        {(error || general) && <p className="form-errors">{error || general}</p>}
        <Button className="full" type="submit">Guardar insumo</Button>
      </form>
    </Panel>
  )
}

export default FormularioInsumo

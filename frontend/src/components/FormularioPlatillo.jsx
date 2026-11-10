import { useState } from 'react'

const VACIO = { nombre: '', precio: '', categoria: '', requiere_receta: true }

// Formulario hijo y controlado: valida con las mismas reglas que la API (HU-07) y,
// si todo está bien, entrega el platillo al padre con onGuardar y vuelve a quedar vacío.
function FormularioPlatillo({ categorias, onGuardar }) {
  const [datos, setDatos] = useState(VACIO)
  const [errores, setErrores] = useState({})

  function cambiar(evento) {
    const { name, value, type, checked } = evento.target
    setDatos({ ...datos, [name]: type === 'checkbox' ? checked : value })
  }

  function validar() {
    const nuevos = {}
    if (datos.nombre.trim() === '') nuevos.nombre = 'El nombre es obligatorio.'
    else if (datos.nombre.trim().length > 150) nuevos.nombre = 'Máximo 150 caracteres.'
    const precio = Number(datos.precio)
    if (datos.precio === '' || Number.isNaN(precio)) nuevos.precio = 'El precio es obligatorio.'
    else if (precio <= 0) nuevos.precio = 'Debe ser mayor que 0.'
    else if (!/^\d+(\.\d{1,2})?$/.test(datos.precio)) nuevos.precio = 'Admite hasta 2 decimales.'
    if (datos.categoria === '') nuevos.categoria = 'Elige una categoría.'
    return nuevos
  }

  function enviar(evento) {
    evento.preventDefault()
    const nuevos = validar()
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) return

    const categoria = categorias.find((c) => c.id === Number(datos.categoria))
    onGuardar({
      nombre: datos.nombre.trim(),
      precio: precio2(datos.precio),
      categoria: categoria.id,
      categoria_nombre: categoria.nombre,
      requiere_receta: datos.requiere_receta,
      estado: 'ACTIVO',
    })
    setDatos(VACIO)
  }

  return (
    <form className="formulario" onSubmit={enviar} noValidate>
      <h3>Nuevo platillo</h3>
      <label>
        Nombre
        <input name="nombre" value={datos.nombre} onChange={cambiar} />
        {errores.nombre && <span className="error">{errores.nombre}</span>}
      </label>
      <label>
        Precio (S/)
        <input name="precio" value={datos.precio} onChange={cambiar} inputMode="decimal" />
        {errores.precio && <span className="error">{errores.precio}</span>}
      </label>
      <label>
        Categoría
        <select name="categoria" value={datos.categoria} onChange={cambiar}>
          <option value="">Elige...</option>
          {categorias.map((categoria) => (
            <option key={categoria.id} value={categoria.id}>
              {categoria.nombre}
            </option>
          ))}
        </select>
        {errores.categoria && <span className="error">{errores.categoria}</span>}
      </label>
      <label className="check">
        <input type="checkbox" name="requiere_receta" checked={datos.requiere_receta} onChange={cambiar} />
        Requiere receta
      </label>
      <button type="submit">Registrar platillo</button>
    </form>
  )
}

// "22" → "22.00": la API guarda el precio como texto con 2 decimales
function precio2(texto) {
  return Number(texto).toFixed(2)
}

export default FormularioPlatillo

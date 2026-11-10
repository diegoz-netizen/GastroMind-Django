// Una fila de la carta. No cambia la lista: avisa al padre con onCambiarEstado y onEliminar.
function FilaPlatillo({ platillo, onCambiarEstado, onEliminar }) {
  const activo = platillo.estado === 'ACTIVO'

  return (
    <li className="fila">
      <span className="nombre">{platillo.nombre}</span>
      <span>{platillo.categoria_nombre}</span>
      <span>S/ {Number(platillo.precio).toFixed(2)}</span>
      <span className={activo ? 'etiqueta' : 'etiqueta agotado'}>{activo ? 'Activo' : 'Inactivo'}</span>
      <button type="button" onClick={() => onCambiarEstado(platillo.id)}>
        {activo ? 'Desactivar' : 'Activar'}
      </button>
      <button type="button" className="peligro" onClick={() => onEliminar(platillo.id)}>
        Eliminar
      </button>
    </li>
  )
}

export default FilaPlatillo

// Lab 10: un insumo con su botón Reservar y su propio contador (useState dentro de la tarjeta).
// Lab 11: ya no guarda estado. Es una fila del listado que avisa al padre con onReservar y onEliminar.
function InsumoCard({ insumo, onReservar, onEliminar }) {
  const unidad = insumo.unidad_medida
  const stock = Number(insumo.stock_actual)
  const agotado = stock === 0

  return (
    <li className="fila">
      <span className="nombre">{insumo.nombre}</span>
      <span>S/ {Number(insumo.costo_unitario).toFixed(2)} por {unidad}</span>
      <span className={agotado ? 'etiqueta agotado' : 'etiqueta'}>
        {agotado ? 'Agotado' : `Stock: ${stock} ${unidad}`}
      </span>
      {insumo.bajo_stock_minimo && !agotado && <span className="aviso">¡Últimas unidades!</span>}
      <button type="button" onClick={() => onReservar(insumo.id)} disabled={agotado}>
        Reservar 1 {unidad}
      </button>
      <button type="button" className="peligro" onClick={() => onEliminar(insumo.id)}>
        Eliminar
      </button>
    </li>
  )
}

export default InsumoCard

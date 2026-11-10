// Hijo: muestra un producto y avisa al padre con onAgregar. No modifica la prop producto.
function ProductoCard({ producto, onAgregar }) {
  const agotado = producto.stock === 0

  return (
    <li className="fila">
      <span className="nombre">{producto.nombre}</span>
      <span>S/ {Number(producto.precio).toFixed(2)}</span>
      {agotado && <span className="etiqueta agotado">Agotado</span>}
      <button type="button" onClick={() => onAgregar(producto)} disabled={agotado}>
        Agregar
      </button>
    </li>
  )
}

export default ProductoCard

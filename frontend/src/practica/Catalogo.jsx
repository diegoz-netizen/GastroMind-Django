import ProductoCard from './ProductoCard'

// Recibe los productos (ya filtrados) y la función onAgregar, y se la pasa a cada tarjeta.
function Catalogo({ productos, onAgregar }) {
  if (productos.length === 0) {
    return <p className="vacio">No hay productos que coincidan</p>
  }

  return (
    <ul className="lista">
      {productos.map((producto) => (
        <ProductoCard key={producto.id} producto={producto} onAgregar={onAgregar} />
      ))}
    </ul>
  )
}

export default Catalogo

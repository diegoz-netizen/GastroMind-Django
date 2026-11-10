import LineaReceta from './LineaReceta'

// Relación 1:N: un platillo con su receta (un LineaReceta por insumo) y el costo calculado (HU-08).
// Los nombres de la API (detalles_receta, cantidad_requerida) se convierten a props de LineaReceta.
function PlatilloCard({ nombre, categoria, precio, lineas }) {
  const costo = lineas.reduce(
    (total, linea) => total + Number(linea.cantidad_requerida) * Number(linea.costo_unitario),
    0,
  )
  const porcentaje = (costo / Number(precio)) * 100

  return (
    <article className="tarjeta">
      <h3>
        {nombre} <small>{categoria}</small>
      </h3>
      {lineas.length === 0 ? (
        <p className="vacio">No lleva receta</p>
      ) : (
        <ul className="sublista">
          {lineas.map((linea) => (
            <LineaReceta
              key={linea.id}
              ingrediente={linea.ingrediente_nombre}
              cantidad={Number(linea.cantidad_requerida)}
              unidad={linea.unidad_medida}
              costoUnitario={Number(linea.costo_unitario)}
            />
          ))}
        </ul>
      )}
      <p className="total">
        Precio S/ {Number(precio).toFixed(2)} · Costo de insumos S/ {costo.toFixed(2)}
      </p>
      <div className="barra">
        <div className="barra-relleno" style={{ width: `${porcentaje}%` }} />
      </div>
      <p className="detalle">{porcentaje.toFixed(1)} % del precio se va en insumos</p>
    </article>
  )
}

export default PlatilloCard

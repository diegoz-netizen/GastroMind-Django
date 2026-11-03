import LineaReceta from './LineaReceta';

// Relación 1:N: un platillo y los insumos de su receta. El costo se calcula como en la API (HU-08):
// Σ cantidad × costo unitario, redondeado una sola vez al final.
function RecetaCard({ nombre, precio, lineas }) {
  const costo = lineas.reduce(
    (suma, linea) => suma + Number(linea.cantidad_requerida) * Number(linea.costo_unitario),
    0,
  );
  const precioNumero = Number(precio);
  const margen = precioNumero - costo;
  const porcentajeCosto = precioNumero > 0 ? (costo / precioNumero) * 100 : 0;

  return (
    <article className="receta">
      <h3>{nombre}</h3>
      <ul>
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
      <p className="totales">
        Costo S/ {costo.toFixed(2)} · Margen S/ {margen.toFixed(2)} · {porcentajeCosto.toFixed(1)} % del precio
      </p>
    </article>
  );
}

export default RecetaCard;

// Un insumo de la receta: cantidad × costo unitario (CA-08).
function LineaReceta({ ingrediente, cantidad, unidad, costoUnitario }) {
  const subtotal = cantidad * costoUnitario;
  return (
    <li className="linea">
      <span>{ingrediente}</span>
      <span className="detalle">
        {cantidad.toFixed(3)} {unidad} × S/ {costoUnitario.toFixed(2)}
      </span>
      <span className="cifra">S/ {subtotal.toFixed(2)}</span>
    </li>
  );
}

export default LineaReceta;

// Un insumo de la receta de un platillo
function LineaReceta({ ingrediente, cantidad, unidad, costoUnitario }) {
  return (
    <li>
      {ingrediente}: {cantidad} {unidad} × S/ {costoUnitario.toFixed(2)}
    </li>
  )
}

export default LineaReceta

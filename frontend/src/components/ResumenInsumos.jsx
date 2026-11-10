import { useEffect } from 'react'

// Lab 11: hermano del listado. Todo se calcula a partir de los insumos que recibe, sin useState.
function ResumenInsumos({ insumos }) {
  const bajoMinimo = insumos.filter((insumo) => insumo.bajo_stock_minimo).length
  const agotados = insumos.filter((insumo) => Number(insumo.stock_actual) === 0).length
  const valorStock = insumos.reduce(
    (suma, insumo) => suma + Number(insumo.stock_actual) * Number(insumo.costo_unitario), 0)

  // El título de la pestaña cambia solo cuando cambia la cantidad de insumos bajo el mínimo
  useEffect(() => {
    document.title = `Insumos (${bajoMinimo} bajo el mínimo) — GastroMind`
  }, [bajoMinimo])

  return (
    <div className="resumen">
      <h3>Resumen del almacén</h3>
      <p>Insumos registrados: {insumos.length}</p>
      <p>Bajo el stock mínimo: {bajoMinimo}</p>
      <p>Agotados: {agotados}</p>
      <p>Valor del stock: S/ {valorStock.toFixed(2)}</p>
    </div>
  )
}

export default ResumenInsumos

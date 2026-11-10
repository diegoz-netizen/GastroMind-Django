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
    <div className="kpis">
      <div className="kpi">
        <small>Insumos registrados</small>
        <strong>{insumos.length}</strong>
      </div>
      <div className={bajoMinimo > 0 ? 'kpi alerta' : 'kpi'}>
        <small>Bajo el stock mínimo</small>
        <strong>{bajoMinimo}</strong>
      </div>
      <div className={agotados > 0 ? 'kpi peligro' : 'kpi'}>
        <small>Agotados</small>
        <strong>{agotados}</strong>
      </div>
      <div className="kpi">
        <small>Valor del stock</small>
        <strong>S/ {valorStock.toFixed(2)}</strong>
      </div>
    </div>
  )
}

export default ResumenInsumos

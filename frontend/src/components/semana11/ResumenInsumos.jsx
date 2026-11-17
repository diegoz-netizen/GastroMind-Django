import { useEffect } from 'react'
import { Metric } from '../../ui'

const dinero = (n) => `S/ ${Number(n).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

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
    <div className="metrics">
      <Metric label="Insumos registrados" value={String(insumos.length)} note="En esta sede" />
      <Metric label="Bajo stock mínimo" value={String(bajoMinimo)} note="Requieren atención" tone="warning" />
      <Metric label="Agotados" value={String(agotados)} note="Sin existencias" tone="danger" />
      <Metric label="Valor del stock" value={dinero(valorStock)} note="Costo total estimado" tone="brand" />
    </div>
  )
}

export default ResumenInsumos

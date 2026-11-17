import { Badge, Icon, Miniatura } from '../../ui'

const dinero = (n) => `S/ ${Number(n).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const cantidad = (n) => Number(n).toLocaleString('es-PE', { maximumFractionDigits: 3 })
const abreviatura = (unidad) => (unidad === 'unidades' ? 'un.' : unidad)

// Lab 10: un insumo con su propio contador (useState dentro de la tarjeta).
// Lab 11: ya no guarda estado: es una fila que solo muestra lo que el padre le pasa por props.
// Lab 12: el insumo llega de la API (GET /api/catalogo/insumos/).
function InsumoCard({ insumo }) {
  const unidad = abreviatura(insumo.unidad_medida)
  const stock = Number(insumo.stock_actual)
  let tono = 'success'
  let aviso = 'Stock saludable'
  if (stock === 0) {
    tono = 'danger'
    aviso = 'Reponer hoy'
  } else if (insumo.bajo_stock_minimo) {
    tono = 'warning'
    aviso = '¡Últimas unidades!'
  }

  return (
    <article className="list-row">
      <Miniatura clase={`product-mark mark-${insumo.id % 4}`} nombre={insumo.nombre} icono={<Icon name="box" size={20} />} />
      <div className="item-primary">
        <strong>{insumo.nombre}</strong>
        <span>Mínimo: {cantidad(insumo.stock_minimo)} {unidad}</span>
      </div>
      <div className="item-data">
        <span>Costo unitario</span>
        <strong className="numeric">{dinero(insumo.costo_unitario)} / {unidad}</strong>
      </div>
      <div className="stock-data">
        <Badge tone={tono}>{stock === 0 ? 'Agotado' : `Stock: ${cantidad(stock)} ${unidad}`}</Badge>
        <small>{aviso}</small>
      </div>
    </article>
  )
}

export default InsumoCard

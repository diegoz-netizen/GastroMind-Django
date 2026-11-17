import { Empty } from '../../ui'
import InsumoCard from './InsumoCard'

// Lab 10: guardaba la lista, la búsqueda y el formulario en su propio estado.
// Lab 11: es solo el listado. Recibe los insumos ya filtrados y se los pasa a cada fila.
function ListaInsumos({ insumos, total }) {
  if (total === 0) return <Empty text="No hay registros." detail="Registra el primer insumo con el formulario." />
  if (insumos.length === 0) return <Empty text="No hay insumos que coincidan." />

  return (
    <div className="item-list">
      {insumos.map((insumo) => (
        <InsumoCard key={insumo.id} insumo={insumo} />
      ))}
    </div>
  )
}

export default ListaInsumos

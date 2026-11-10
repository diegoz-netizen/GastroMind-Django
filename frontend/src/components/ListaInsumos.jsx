import InsumoCard from './InsumoCard'

// Lab 10: guardaba la lista, la búsqueda y el formulario en su propio estado.
// Lab 11: es solo el listado. Recibe los insumos ya filtrados y las funciones del padre, y se las pasa a cada fila.
function ListaInsumos({ insumos, total, onReservar, onEliminar }) {
  if (total === 0) {
    return <p className="vacio">No hay registros</p>
  }
  if (insumos.length === 0) {
    return <p className="vacio">No hay insumos que coincidan</p>
  }

  return (
    <ul className="lista">
      {insumos.map((insumo) => (
        <InsumoCard key={insumo.id} insumo={insumo} onReservar={onReservar} onEliminar={onEliminar} />
      ))}
    </ul>
  )
}

export default ListaInsumos

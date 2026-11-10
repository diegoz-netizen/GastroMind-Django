import FilaPlatillo from './FilaPlatillo'

// Dibuja una fila por platillo y les pasa las funciones del padre.
function ListadoPlatillos({ platillos, onCambiarEstado, onEliminar }) {
  if (platillos.length === 0) {
    return <p className="vacio">No hay platillos que coincidan</p>
  }

  return (
    <ul className="lista">
      {platillos.map((platillo) => (
        <FilaPlatillo
          key={platillo.id}
          platillo={platillo}
          onCambiarEstado={onCambiarEstado}
          onEliminar={onEliminar}
        />
      ))}
    </ul>
  )
}

export default ListadoPlatillos

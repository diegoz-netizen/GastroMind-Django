import { useEffect } from 'react'

// Hermano del listado: todo se calcula a partir de la lista que recibe, sin useState.
function ResumenCarta({ platillos }) {
  const activos = platillos.filter((platillo) => platillo.estado === 'ACTIVO').length
  const inactivos = platillos.length - activos
  const precioPromedio = platillos.length === 0
    ? 0
    : platillos.reduce((suma, platillo) => suma + Number(platillo.precio), 0) / platillos.length

  // El título de la pestaña cambia solo cuando cambia la cantidad de platillos activos
  useEffect(() => {
    document.title = `Carta (${activos} activos) — GastroMind`
  }, [activos])

  return (
    <div className="resumen">
      <h3>Resumen de la carta</h3>
      <p>Platillos: {platillos.length}</p>
      <p>Activos (salen en la toma de pedidos): {activos}</p>
      <p>Inactivos: {inactivos}</p>
      <p>Precio promedio: S/ {precioPromedio.toFixed(2)}</p>
    </div>
  )
}

export default ResumenCarta

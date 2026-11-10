import { useEffect } from 'react'

// Hermano del catálogo: recibe las líneas del carrito por props y avisa al padre para quitar o vaciar.
function Carrito({ lineas, onQuitar, onVaciar }) {
  // Datos derivados: se calculan en cada dibujo a partir de las líneas, sin useState
  const total = lineas.reduce((suma, linea) => suma + Number(linea.precio) * linea.cantidad, 0)
  const unidades = lineas.reduce((suma, linea) => suma + linea.cantidad, 0)

  // Se ejecuta al montar y cada vez que cambia la cantidad de unidades
  useEffect(() => {
    console.log('Efecto del carrito: unidades =', unidades)
    document.title = `Carrito (${unidades}) — Cafetería`
  }, [unidades])

  return (
    <div className="carrito">
      <h3>Carrito</h3>
      {lineas.length === 0 && <p className="vacio">El carrito está vacío</p>}
      {lineas.length > 0 && (
        <>
          <ul className="lista">
            {lineas.map((linea) => (
              <li key={linea.id} className="fila">
                <span className="nombre">{linea.nombre}</span>
                <span>
                  {linea.cantidad} × S/ {Number(linea.precio).toFixed(2)}
                </span>
                <button type="button" onClick={() => onQuitar(linea.id)}>
                  Quitar
                </button>
              </li>
            ))}
          </ul>
          <p className="total">
            Unidades: {unidades} · Total: S/ {total.toFixed(2)}
          </p>
          <button type="button" onClick={onVaciar}>
            Vaciar carrito
          </button>
        </>
      )}
    </div>
  )
}

export default Carrito

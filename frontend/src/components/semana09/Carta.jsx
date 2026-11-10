import { platillos } from '../../datos'
import Tarjeta from '../compartido/Tarjeta'
import PlatilloCard from '../semana10/PlatilloCard'

// Semana 09: JSX con expresiones entre llaves (cantidad de platillos, precio con IGV) y lista con map + key.
// En la Semana 10 cada platillo pasó a dibujarse con su componente PlatilloCard (props).
const IGV = 0.18

function precioConIgv(precio) {
  return (Number(precio) * (1 + IGV)).toFixed(2)
}

function Carta() {
  const lomo = platillos[1]

  return (
    <div>
      <p className="resumen-modulo">
        {platillos.length} platillos en la carta · {lomo.nombre} con IGV: S/ {precioConIgv(lomo.precio)}
      </p>

      <Tarjeta titulo="Platillos y su receta">
        <div className="platillos">
          {platillos.map((platillo) => (
            <PlatilloCard
              key={platillo.id}
              nombre={platillo.nombre}
              categoria={platillo.categoria_nombre}
              precio={platillo.precio}
              lineas={platillo.detalles_receta}
            />
          ))}
        </div>
      </Tarjeta>
    </div>
  )
}

export default Carta

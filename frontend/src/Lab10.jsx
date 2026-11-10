import { empleados, insumos, platillos, restaurantes } from './datos'
import ListaEmpleados from './components/ListaEmpleados'
import ListaInsumos from './components/ListaInsumos'
import PlatilloCard from './components/PlatilloCard'
import RestauranteCard from './components/RestauranteCard'
import Tarjeta from './components/Tarjeta'

// Laboratorio 10: la interfaz del Laboratorio 09 reorganizada en componentes (src/components)
// que reciben sus datos por props, con estado (useState) y eventos. Desde el Lab 11 se abre desde App.

const nombreApp = 'GastroMind'
const IGV = 0.18

function precioConIgv(precio) {
  return (Number(precio) * (1 + IGV)).toFixed(2)
}

function Lab10() {
  const sede = 'Sede Central'
  const lomo = platillos[1]

  return (
    <div>
      <header className="encabezado">
        <h1>{nombreApp}: catálogo de la {sede}</h1>
        <p>
          {platillos.length} platillos en la carta · {lomo.nombre} con IGV: S/ {precioConIgv(lomo.precio)}
        </p>
      </header>

      <h2 className="parte">Parte 1: catálogo</h2>

      <Tarjeta titulo="Insumos">
        <ListaInsumos insumos={insumos} />
      </Tarjeta>

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

      <h2 className="parte">Parte 2: personal</h2>

      <Tarjeta titulo="Empleados">
        <ListaEmpleados empleados={empleados} restaurantes={restaurantes} />
      </Tarjeta>

      <Tarjeta titulo="Personal por restaurante">
        {restaurantes.map((restaurante) => (
          <RestauranteCard
            key={restaurante.id}
            nombre={restaurante.nombre}
            personal={empleados.filter((empleado) => empleado.restauranteId === restaurante.id)}
          />
        ))}
      </Tarjeta>
    </div>
  )
}

export default Lab10

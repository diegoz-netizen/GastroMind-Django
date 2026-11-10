import { empleados, restaurantes } from '../../datos'
import Tarjeta from '../compartido/Tarjeta'
import ListaEmpleados from './ListaEmpleados'
import RestauranteCard from './RestauranteCard'

// Semana 10: componentes con props, estado (useState) y eventos. ListaEmpleados tiene el buscador
// y el formulario controlado; RestauranteCard muestra la relación 1:N (sede con su personal).
function Personal() {
  return (
    <div>
      <Tarjeta titulo="Empleados">
        <ListaEmpleados empleados={empleados} restaurantes={restaurantes} />
      </Tarjeta>

      <Tarjeta titulo="Personal por restaurante">
        <div className="platillos">
          {restaurantes.map((restaurante) => (
            <RestauranteCard
              key={restaurante.id}
              nombre={restaurante.nombre}
              personal={empleados.filter((empleado) => empleado.restauranteId === restaurante.id)}
            />
          ))}
        </div>
      </Tarjeta>
    </div>
  )
}

export default Personal

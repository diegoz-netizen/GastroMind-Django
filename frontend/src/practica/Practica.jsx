import { useState } from 'react'
import { productos } from './datos'
import { platillos } from '../datos'
import PlatilloCard from '../components/semana10/PlatilloCard'
import Tarjeta from '../components/compartido/Tarjeta'
import Aviso from './Aviso'
import Buscador from './Buscador'
import Carrito from './Carrito'
import Catalogo from './Catalogo'

function Practica() {
  const [carrito, setCarrito] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [aviso, setAviso] = useState(null)

  function agregarAlCarrito(producto) {
    console.log('Agregar:', producto.nombre)
    const yaEsta = carrito.some((linea) => linea.id === producto.id)
    if (yaEsta) {
      setCarrito(carrito.map((linea) =>
        linea.id === producto.id ? { ...linea, cantidad: linea.cantidad + 1 } : linea))
    } else {
      setCarrito([...carrito, { id: producto.id, nombre: producto.nombre, precio: producto.precio, cantidad: 1 }])
    }
    setAviso(`Agregado: ${producto.nombre}`)
  }

  function quitarDelCarrito(id) {
    setCarrito(carrito.filter((linea) => linea.id !== id))
  }

  function vaciarCarrito() {
    setCarrito([])
  }

  const texto = busqueda.trim().toLowerCase()
  const visibles = productos.filter((producto) => producto.nombre.toLowerCase().includes(texto))

  return (
    <section className="seccion">
      <h2>Parte 1: mini catálogo con carrito</h2>

      {/* Ejercicio 1 con los componentes del Lab 10: Practica (padre) → Tarjeta → PlatilloCard → LineaReceta */}
      <Tarjeta titulo="Ejercicio 1: platillos de la carta (componentes del Lab 10)">
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

      {aviso && <Aviso mensaje={aviso} onCerrar={setAviso} />}
      <div className="practica">
        <div>
          <Buscador valor={busqueda} onCambiar={setBusqueda} />
          <Catalogo productos={visibles} onAgregar={agregarAlCarrito} />
        </div>
        <Carrito lineas={carrito} onQuitar={quitarDelCarrito} onVaciar={vaciarCarrito} />
      </div>
    </section>
  )
}

export default Practica

import { useState } from 'react'
import { productos } from './datos'
import Aviso from './Aviso'
import Buscador from './Buscador'
import Carrito from './Carrito'
import Catalogo from './Catalogo'

// Padre de la Parte 1: guarda el carrito, el texto de búsqueda y el aviso (estado elevado),
// los entrega a los hijos por props y recibe sus avisos con funciones.
function Practica() {
  const [carrito, setCarrito] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [aviso, setAviso] = useState(null)

  function agregarAlCarrito(producto) {
    console.log('Agregar:', producto.nombre)
    const yaEsta = carrito.some((linea) => linea.id === producto.id)
    if (yaEsta) {
      // Arreglo nuevo con map(): solo cambia la línea de ese producto
      setCarrito(carrito.map((linea) =>
        linea.id === producto.id ? { ...linea, cantidad: linea.cantidad + 1 } : linea))
    } else {
      // Arreglo nuevo con spread (sin push)
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

  // Lo que se entrega al catálogo depende de la búsqueda (sin estado nuevo)
  const texto = busqueda.trim().toLowerCase()
  const visibles = productos.filter((producto) => producto.nombre.toLowerCase().includes(texto))

  return (
    <section className="seccion">
      <h2>Parte 1: mini catálogo con carrito</h2>
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

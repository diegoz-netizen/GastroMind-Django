import { useState } from 'react'
import { categorias, platillosIniciales } from '../datosCarta'
import AvisoPanel from './AvisoPanel'
import FiltroCarta from './FiltroCarta'
import FormularioPlatillo from './FormularioPlatillo'
import ListadoPlatillos from './ListadoPlatillos'
import ResumenCarta from './ResumenCarta'

// Padre de la pantalla "Carta" del panel administrativo. Aquí vive el estado de la carta:
// los platillos, el filtro y el aviso. Los hijos lo reciben por props y avisan con funciones.
function PanelPlatillos() {
  const [platillos, setPlatillos] = useState(platillosIniciales)
  const [texto, setTexto] = useState('')
  const [estado, setEstado] = useState('TODOS')
  const [aviso, setAviso] = useState(null)

  // map(): arreglo nuevo con el platillo cambiado (como PATCH /productos/{id}/estado/ de HU-07)
  function cambiarEstado(id) {
    setPlatillos(platillos.map((platillo) =>
      platillo.id === id
        ? { ...platillo, estado: platillo.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO' }
        : platillo))
  }

  // filter(): arreglo nuevo sin ese platillo
  function eliminar(id) {
    setPlatillos(platillos.filter((platillo) => platillo.id !== id))
  }

  // spread: arreglo nuevo con el platillo del formulario al final (como POST /productos/)
  function guardar(nuevo) {
    const id = platillos.reduce((mayor, platillo) => Math.max(mayor, platillo.id), 0) + 1
    setPlatillos([...platillos, { ...nuevo, id, costo: '0.00', porcentaje_costo: null }])
    setAviso(`Platillo registrado: ${nuevo.nombre}`)
  }

  // Lo que ve el listado sale del estado + el filtro, sin guardarlo aparte
  const buscado = texto.trim().toLowerCase()
  const visibles = platillos.filter((platillo) =>
    platillo.nombre.toLowerCase().includes(buscado) && (estado === 'TODOS' || platillo.estado === estado))

  return (
    <section className="seccion">
      <h2>Parte 2: carta de la Sede Central (panel administrativo)</h2>
      {aviso && <AvisoPanel mensaje={aviso} onCerrar={setAviso} />}
      <div className="panel">
        <div>
          <FiltroCarta texto={texto} estado={estado} onCambiarTexto={setTexto} onCambiarEstado={setEstado} />
          <ListadoPlatillos platillos={visibles} onCambiarEstado={cambiarEstado} onEliminar={eliminar} />
        </div>
        <div>
          <ResumenCarta platillos={platillos} />
          <FormularioPlatillo categorias={categorias} onGuardar={guardar} />
        </div>
      </div>
    </section>
  )
}

export default PanelPlatillos

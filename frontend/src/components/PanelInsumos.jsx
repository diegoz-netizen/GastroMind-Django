import { useState } from 'react'
import { insumos as insumosIniciales } from '../datos'
import AvisoPanel from './AvisoPanel'
import BuscadorInsumos from './BuscadorInsumos'
import FormularioInsumo from './FormularioInsumo'
import ListaInsumos from './ListaInsumos'
import ResumenInsumos from './ResumenInsumos'
import Tarjeta from './Tarjeta'

// Lab 11: padre de la pantalla "Insumos" del panel administrativo. Aquí vive el estado que en el Lab 10
// estaba repartido entre ListaInsumos e InsumoCard: los insumos, la búsqueda y el aviso.
function PanelInsumos() {
  const [insumos, setInsumos] = useState(insumosIniciales)
  const [busqueda, setBusqueda] = useState('')
  const [aviso, setAviso] = useState(null)

  // map(): arreglo nuevo en el que solo ese insumo baja 1 unidad de stock
  function reservar(id) {
    setInsumos(insumos.map((insumo) => {
      if (insumo.id !== id) return insumo
      const stock = Math.max(0, Number(insumo.stock_actual) - 1)
      return { ...insumo, stock_actual: stock.toFixed(2), bajo_stock_minimo: stock <= Number(insumo.stock_minimo) }
    }))
  }

  // filter(): arreglo nuevo sin ese insumo
  function eliminar(id) {
    setInsumos(insumos.filter((insumo) => insumo.id !== id))
  }

  // spread: arreglo nuevo con el insumo del formulario al final (como POST /api/catalogo/insumos/)
  function guardar(nuevo) {
    const id = Math.max(0, ...insumos.map((insumo) => insumo.id)) + 1
    setInsumos([...insumos, { ...nuevo, id }])
    setAviso(`Insumo registrado: ${nuevo.nombre}`)
  }

  // Lo que ve el listado sale del estado + la búsqueda, sin guardarlo aparte
  const texto = busqueda.trim().toLowerCase()
  const visibles = insumos.filter((insumo) => insumo.nombre.toLowerCase().includes(texto))
  const nombresUsados = insumos.map((insumo) => insumo.nombre.toLowerCase())

  return (
    <Tarjeta titulo="Parte 2: insumos de la Sede Central (panel administrativo)">
      {aviso && <AvisoPanel mensaje={aviso} onCerrar={setAviso} />}
      <div className="panel">
        <div>
          <BuscadorInsumos valor={busqueda} onCambiar={setBusqueda} />
          <ListaInsumos insumos={visibles} total={insumos.length} onReservar={reservar} onEliminar={eliminar} />
        </div>
        <div>
          <ResumenInsumos insumos={insumos} />
          <FormularioInsumo nombresUsados={nombresUsados} onGuardar={guardar} />
        </div>
      </div>
    </Tarjeta>
  )
}

export default PanelInsumos

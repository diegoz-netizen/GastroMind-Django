import { useState } from 'react'
import api, { sesion } from '../semana12/api'
import { camposDeError, mensajeGeneral } from '../semana12/errores'
import { useCargar } from '../semana12/hooks'
import { Button, Cargando, ErrorCarga, PageTitle, Panel } from '../../ui'
import AvisoPanel from './AvisoPanel'
import BuscadorInsumos from './BuscadorInsumos'
import FormularioInsumo from './FormularioInsumo'
import ListaInsumos from './ListaInsumos'
import ResumenInsumos from './ResumenInsumos'

const ROLES_QUE_ESCRIBEN = ['ADMINISTRADOR', 'ALMACENERO']

// Lab 11: padre de la pantalla "Insumos" del panel administrativo. Aquí vive el estado que en el Lab 10
// estaba repartido entre ListaInsumos e InsumoCard: los insumos, la búsqueda y el aviso.
// Lab 12: los insumos ya no vienen de datos.js: se piden a la API (useCargar) y el alta hace POST.
// La API no permite editar ni borrar insumos (el Kardex los referencia), por eso no hay Reservar ni Eliminar.
function PanelInsumos() {
  const { datos: insumos, setDatos, cargando, error, recargar } = useCargar(async () => (await api.get('/insumos/')).data)
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState('Todos')
  const [aviso, setAviso] = useState(null)
  const [errores, setErrores] = useState({})
  const [general, setGeneral] = useState('')
  const puedeEscribir = ROLES_QUE_ESCRIBEN.includes(sesion.usuario()?.rol)

  if (cargando && !insumos) return <Cargando texto="Cargando insumos…" />
  if (error || !insumos) return <ErrorCarga onReintentar={recargar} />

  // spread: arreglo nuevo con el insumo que devolvió la API (POST /api/catalogo/insumos/ → 201)
  async function guardar(nuevo) {
    setErrores({})
    setGeneral('')
    try {
      const respuesta = await api.post('/insumos/', nuevo)
      setDatos([...insumos, respuesta.data])
      setAviso(`${respuesta.data.nombre} se agregó al almacén.`)
      return true
    } catch (err) {
      setErrores(camposDeError(err))
      setGeneral(mensajeGeneral(err))
      return false
    }
  }

  // Lo que ve el listado sale del estado + la búsqueda + el filtro, sin guardarlo aparte
  const texto = busqueda.trim().toLowerCase()
  const visibles = insumos.filter((insumo) =>
    insumo.nombre.toLowerCase().includes(texto) && (filtro === 'Todos' || insumo.bajo_stock_minimo))
  const nombresUsados = insumos.map((insumo) => insumo.nombre.toLowerCase())

  return (
    <>
      <PageTitle eyebrow="Almacén" title="Insumos" subtitle="Controla existencias, costos y niveles mínimos de la sede."
        action={puedeEscribir && <Button icon="plus" onClick={() => document.querySelector('input[name="nombre"]')?.focus()}>Nuevo insumo</Button>} />
      {aviso && <AvisoPanel titulo="Insumo registrado" mensaje={aviso} onCerrar={setAviso} />}
      <ResumenInsumos insumos={insumos} />
      <div className="split-layout">
        <section className="content-card">
          <div className="card-toolbar toolbar-wrap">
            <BuscadorInsumos valor={busqueda} onCambiar={setBusqueda} />
            <div className="segmented">
              {['Todos', 'Bajo mínimo'].map((f) => (
                <button type="button" key={f} className={filtro === f ? 'active' : ''} onClick={() => setFiltro(f)}>{f}</button>
              ))}
            </div>
            <span className="count">{visibles.length} de {insumos.length} insumos</span>
          </div>
          <ListaInsumos insumos={visibles} total={insumos.length} />
        </section>
        {puedeEscribir ? (
          <FormularioInsumo nombresUsados={nombresUsados} onGuardar={guardar} errores={errores} general={general} />
        ) : (
          <Panel title="Solo lectura" subtitle="Tu rol no puede registrar insumos.">
            <p className="field-help">Los insumos los registra el administrador o el almacenero.</p>
          </Panel>
        )}
      </div>
    </>
  )
}

export default PanelInsumos

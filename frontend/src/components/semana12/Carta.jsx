import { useRef, useState } from 'react'
import api, { sesion } from './api'
import { useCargar } from './hooks'
import { Badge, Button, Cargando, Empty, ErrorCarga, Field, Metric, Miniatura, PageTitle, Panel, Search, Toast, Icon } from '../../ui'
import { camposDeError, mensajeGeneral, mensajesDeError } from './errores'

const FORM_VACIO = { nombre: '', precio: '', categoria: '', requiere_receta: true }
const dinero = (n) => `S/ ${Number(n).toFixed(2)}`

// Margen = lo que queda del precio después del costo de insumos; solo lo ve el administrador y si hay receta
const margen = (p) => (p.porcentaje_costo == null ? null : Math.round(100 - Number(p.porcentaje_costo)))

// Gestión de carta (HU-07): lista, alta, edición y activar/desactivar. Un platillo no se borra (CA-07).
function Carta() {
  const { datos, setDatos, cargando, error, recargar } = useCargar(async () => {
    const [productos, categorias] = await Promise.all([api.get('/productos/'), api.get('/categorias/')])
    return { platillos: productos.data, categorias: categorias.data }
  })
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState('Todos')
  const [confirmar, setConfirmar] = useState(null)
  const [editando, setEditando] = useState(null)
  const [form, setForm] = useState(FORM_VACIO)
  const [errores, setErrores] = useState({})
  const [general, setGeneral] = useState('')
  const [aviso, setAviso] = useState(null)
  const nombreRef = useRef(null)
  const puedeEscribir = sesion.usuario()?.rol === 'ADMINISTRADOR'

  if (cargando && !datos) return <Cargando texto="Cargando la carta…" />
  if (error || !datos) return <ErrorCarga onReintentar={recargar} />
  const { platillos, categorias } = datos
  const poner = (lista) => setDatos({ ...datos, platillos: lista })

  const activos = platillos.filter((p) => p.estado === 'ACTIVO').length
  const promedio = platillos.length ? platillos.reduce((s, p) => s + Number(p.precio), 0) / platillos.length : 0
  const texto = busqueda.trim().toLowerCase()
  const visibles = platillos.filter((p) => {
    const coincide = p.nombre.toLowerCase().includes(texto)
    return coincide && (filtro === 'Todos' || (filtro === 'Activos') === (p.estado === 'ACTIVO'))
  })

  function cambiarCampo(evento) {
    const { name, value, type, checked } = evento.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  function nuevo() {
    setEditando(null)
    setForm(FORM_VACIO)
    setErrores({})
    setGeneral('')
    nombreRef.current?.focus()
  }

  function editar(p) {
    setEditando(p)
    setForm({ nombre: p.nombre, precio: p.precio, categoria: p.categoria, requiere_receta: p.requiere_receta })
    setErrores({})
    setGeneral('')
    nombreRef.current?.focus()
  }

  async function guardar(evento) {
    evento.preventDefault()
    setErrores({})
    setGeneral('')
    const cuerpo = { nombre: form.nombre, precio: form.precio, categoria: form.categoria, requiere_receta: form.requiere_receta }
    try {
      if (editando) {
        const r = await api.patch(`/productos/${editando.id}/`, cuerpo)
        poner(platillos.map((p) => (p.id === editando.id ? r.data : p)))
        setAviso({ titulo: 'Platillo actualizado', texto: `${r.data.nombre} se guardó correctamente.` })
      } else {
        const r = await api.post('/productos/', cuerpo)
        poner([...platillos, r.data])
        setAviso({ titulo: 'Platillo creado', texto: `${r.data.nombre} ya está en la carta.` })
      }
      setForm(FORM_VACIO)
      setEditando(null)
    } catch (err) {
      setErrores(camposDeError(err))
      setGeneral(mensajeGeneral(err))
    }
  }

  // PATCH /productos/{id}/estado/. Si ya no existe (404) se avisa y se quita de la lista
  async function cambiarEstado(p) {
    setConfirmar(null)
    const nuevoEstado = p.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO'
    try {
      const r = await api.patch(`/productos/${p.id}/estado/`, { estado: nuevoEstado })
      poner(platillos.map((x) => (x.id === p.id ? r.data : x)))
      setAviso({ titulo: nuevoEstado === 'ACTIVO' ? 'Platillo activado' : 'Platillo desactivado', texto: `${p.nombre} ahora está ${nuevoEstado === 'ACTIVO' ? 'activo' : 'inactivo'}.` })
    } catch (err) {
      if (err.response?.status === 404) {
        poner(platillos.filter((x) => x.id !== p.id))
        setGeneral('El platillo ya no existe en el servidor.')
      } else {
        setGeneral(mensajesDeError(err)[0])
      }
    }
  }

  return (
    <>
      <PageTitle eyebrow="Carta" title="Gestión de carta" subtitle="Administra la oferta, precios y disponibilidad de tus platillos."
        action={puedeEscribir && <Button icon="plus" onClick={nuevo}>Nuevo platillo</Button>} />
      {aviso && <Toast titulo={aviso.titulo} texto={aviso.texto} onCerrar={() => setAviso(null)} />}
      <div className="metrics">
        <Metric label="Platillos" value={String(platillos.length)} note={`En ${categorias.length} categorías`} />
        <Metric label="Activos" value={String(activos)} note="Disponibles para pedido" tone="success" />
        <Metric label="Inactivos" value={String(platillos.length - activos)} note="Ocultos temporalmente" tone="neutral" />
        <Metric label="Precio promedio" value={dinero(promedio)} note="Carta actual" tone="brand" />
      </div>
      <div className="split-layout">
        <section className="content-card">
          <div className="card-toolbar toolbar-wrap">
            <Search value={busqueda} onChange={setBusqueda} placeholder="Buscar platillo" />
            <div className="segmented">
              {['Todos', 'Activos', 'Inactivos'].map((f) => (
                <button type="button" key={f} className={filtro === f ? 'active' : ''} onClick={() => setFiltro(f)}>{f}</button>
              ))}
            </div>
          </div>
          <div className="table-head dish-grid">
            <span>Platillo</span>
            <span>Precio</span>
            <span>Margen</span>
            <span>Estado</span>
            <span>Acciones</span>
          </div>
          <div className="item-list">
            {visibles.length ? (
              visibles.map((p, i) => {
                const activo = p.estado === 'ACTIVO'
                const m = margen(p)
                return (
                  <div key={p.id}>
                    {confirmar === p.id && (
                      <div className="inline-confirm">
                        <span className="confirm-icon"><Icon name="alert" size={18} /></span>
                        <p>
                          <strong>¿{activo ? 'Desactivar' : 'Activar'} “{p.nombre}”?</strong>
                          <small>{activo ? 'Dejará de estar disponible para nuevos pedidos.' : 'Volverá a mostrarse en el catálogo.'}</small>
                        </p>
                        <Button variant="secondary" onClick={() => setConfirmar(null)}>Cancelar</Button>
                        <Button variant={activo ? 'danger' : 'primary'} onClick={() => cambiarEstado(p)}>Sí, {activo ? 'desactivar' : 'activar'}</Button>
                      </div>
                    )}
                    <article className="list-row dish-grid">
                      <div className="dish-name">
                        <Miniatura clase={`dish-thumb food-${i % 4}`} nombre={p.nombre} />
                        <p>
                          <strong>{p.nombre}</strong>
                          <small>{p.categoria_nombre}</small>
                        </p>
                      </div>
                      <strong className="numeric">{dinero(p.precio)}</strong>
                      <span className="margin numeric">{m == null ? '—' : `${m}%`}</span>
                      <Badge tone={activo ? 'success' : 'neutral'}>{activo ? 'Activo' : 'Inactivo'}</Badge>
                      <div className="row-actions">
                        {puedeEscribir && (
                          <>
                            <Button variant="ghost" icon="edit" onClick={() => editar(p)}>Editar</Button>
                            <Button variant="ghost" icon="power" onClick={() => setConfirmar(p.id)}>{activo ? 'Desactivar' : 'Activar'}</Button>
                          </>
                        )}
                      </div>
                    </article>
                  </div>
                )
              })
            ) : (
              <Empty text="No hay platillos para mostrar." />
            )}
          </div>
        </section>
        {puedeEscribir ? (
          <Panel title={editando ? 'Editar platillo' : 'Nuevo platillo'} subtitle={editando ? `Estás editando “${editando.nombre}”.` : 'Añade una opción a la carta.'}>
            <form onSubmit={guardar} noValidate>
              <Field label="Nombre" error={errores.nombre}>
                <input ref={nombreRef} name="nombre" value={form.nombre} onChange={cambiarCampo} placeholder="Ej. Tallarines verdes" maxLength={150} />
              </Field>
              <Field label="Precio de venta" error={errores.precio}>
                <div className="input-prefix">
                  <span>S/</span>
                  <input name="precio" type="number" step="0.01" value={form.precio} onChange={cambiarCampo} placeholder="0.00" />
                </div>
              </Field>
              <Field label="Categoría" error={errores.categoria}>
                <select name="categoria" value={form.categoria} onChange={cambiarCampo}>
                  <option value="" disabled>Selecciona una categoría</option>
                  {categorias.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
              </Field>
              <label className="switch-row">
                <span>
                  <strong>Lleva receta</strong>
                  <small>Permite calcular el costo del platillo.</small>
                </span>
                <input name="requiere_receta" type="checkbox" checked={form.requiere_receta} onChange={cambiarCampo} />
                <i />
              </label>
              {general && <p className="form-errors">{general}</p>}
              <div className="form-actions">
                <Button className="full" type="submit">{editando ? 'Guardar cambios' : 'Guardar platillo'}</Button>
                {editando && <Button className="full" variant="secondary" type="button" onClick={nuevo}>Cancelar edición</Button>}
              </div>
            </form>
          </Panel>
        ) : (
          <Panel title="Solo lectura" subtitle="Tu rol no puede editar la carta.">
            <p className="field-help">La carta la administra el administrador.</p>
          </Panel>
        )}
      </div>
    </>
  )
}

export default Carta

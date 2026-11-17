import { useRef, useState } from 'react'
import api, { sesion } from './api'
import { useCargar } from './hooks'
import { Button, Cargando, Empty, ErrorCarga, Field, Icon, PageTitle, Panel, Search, Toast } from '../../ui'
import { camposDeError, mensajeGeneral, mensajesDeError } from './errores'

// Categorías de la carta: CRUD completo. Borrar una categoría con platillos responde 409.
function Categorias() {
  const { datos, setDatos, cargando, error, recargar } = useCargar(async () => {
    const [categorias, productos] = await Promise.all([api.get('/categorias/'), api.get('/productos/')])
    return { categorias: categorias.data, productos: productos.data }
  })
  const [busqueda, setBusqueda] = useState('')
  const [nombre, setNombre] = useState('')
  const [editando, setEditando] = useState(null)
  const [errores, setErrores] = useState({})
  const [general, setGeneral] = useState('')
  const [confirmar, setConfirmar] = useState(null)
  const [conflicto, setConflicto] = useState(null)
  const [aviso, setAviso] = useState(null)
  const nombreRef = useRef(null)
  const puedeEscribir = sesion.usuario()?.rol === 'ADMINISTRADOR'

  if (cargando && !datos) return <Cargando texto="Cargando categorías…" />
  if (error || !datos) return <ErrorCarga onReintentar={recargar} />
  const { categorias, productos } = datos
  const poner = (lista) => setDatos({ ...datos, categorias: lista })
  const cuantos = (id) => productos.filter((p) => p.categoria === id).length
  const texto = busqueda.trim().toLowerCase()
  const visibles = categorias.filter((c) => c.nombre.toLowerCase().includes(texto))

  function nueva() {
    setEditando(null)
    setNombre('')
    setErrores({})
    setGeneral('')
    nombreRef.current?.focus()
  }

  function editar(c) {
    setEditando(c)
    setNombre(c.nombre)
    setErrores({})
    setGeneral('')
    nombreRef.current?.focus()
  }

  async function guardar(evento) {
    evento.preventDefault()
    setErrores({})
    setGeneral('')
    try {
      if (editando) {
        const r = await api.patch(`/categorias/${editando.id}/`, { nombre })
        poner(categorias.map((c) => (c.id === editando.id ? r.data : c)))
        setAviso({ titulo: 'Categoría actualizada', texto: `Ahora se llama “${r.data.nombre}”.` })
      } else {
        const r = await api.post('/categorias/', { nombre })
        poner([...categorias, r.data])
        setAviso({ titulo: 'Categoría creada', texto: `“${r.data.nombre}” ya está disponible.` })
      }
      setNombre('')
      setEditando(null)
    } catch (err) {
      setErrores(camposDeError(err))
      setGeneral(mensajeGeneral(err))
    }
  }

  // DELETE: 204 la quita; 409 si tiene platillos; 404 si ya no existe
  async function eliminar(c) {
    setConfirmar(null)
    setConflicto(null)
    try {
      await api.delete(`/categorias/${c.id}/`)
      poner(categorias.filter((x) => x.id !== c.id))
      setAviso({ titulo: 'Categoría eliminada', texto: `“${c.nombre}” se eliminó.` })
    } catch (err) {
      if (err.response?.status === 404) {
        poner(categorias.filter((x) => x.id !== c.id))
        setGeneral('La categoría ya no existe en el servidor.')
      } else if (err.response?.status === 409) {
        setConflicto({ id: c.id, nombre: c.nombre, mensaje: mensajesDeError(err)[0] })
      } else {
        setGeneral(mensajesDeError(err)[0])
      }
    }
  }

  return (
    <>
      <PageTitle eyebrow="Configuración" title="Categorías" subtitle="Organiza los platillos para mantener una carta clara."
        action={puedeEscribir && <Button icon="plus" onClick={nueva}>Nueva categoría</Button>} />
      {aviso && <Toast titulo={aviso.titulo} texto={aviso.texto} onCerrar={() => setAviso(null)} />}
      <div className="split-layout compact-page">
        <section className="content-card">
          <div className="card-toolbar">
            <Search value={busqueda} onChange={setBusqueda} placeholder="Buscar categoría" />
            <span className="count">{categorias.length} categorías</span>
          </div>
          <div className="item-list">
            {visibles.length ? (
              visibles.map((c, i) => (
                <div key={c.id}>
                  {conflicto?.id === c.id && (
                    <div className="conflict-alert">
                      <Icon name="alert" />
                      <div>
                        <strong>No se puede eliminar “{c.nombre}”</strong>
                        <p>{conflicto.mensaje}</p>
                      </div>
                      <button type="button" onClick={() => setConflicto(null)} aria-label="Cerrar"><Icon name="x" size={17} /></button>
                    </div>
                  )}
                  {confirmar === c.id && (
                    <div className="inline-confirm">
                      <span className="confirm-icon"><Icon name="alert" size={18} /></span>
                      <p>
                        <strong>¿Eliminar “{c.nombre}”?</strong>
                        <small>Esta acción no se puede deshacer.</small>
                      </p>
                      <Button variant="secondary" onClick={() => setConfirmar(null)}>Cancelar</Button>
                      <Button variant="danger" onClick={() => eliminar(c)}>Sí, eliminar</Button>
                    </div>
                  )}
                  <article className="list-row category-row">
                    <span className={`category-icon cat-${i % 4}`}><Icon name="tag" /></span>
                    <div className="item-primary">
                      <strong>{c.nombre}</strong>
                      <span>{cuantos(c.id)} {cuantos(c.id) === 1 ? 'platillo' : 'platillos'}</span>
                    </div>
                    <div className="row-actions">
                      {puedeEscribir && (
                        <>
                          <Button variant="ghost" icon="edit" onClick={() => editar(c)}>Editar</Button>
                          <Button variant="ghost" icon="trash" onClick={() => setConfirmar(c.id)}>Eliminar</Button>
                        </>
                      )}
                    </div>
                  </article>
                </div>
              ))
            ) : (
              <Empty text="No hay categorías para mostrar." />
            )}
          </div>
        </section>
        {puedeEscribir ? (
          <Panel title={editando ? 'Editar categoría' : 'Nueva categoría'} subtitle={editando ? `Estás editando “${editando.nombre}”.` : 'Crea una sección para tu carta.'}>
            <form onSubmit={guardar} noValidate>
              <Field label="Nombre de la categoría" help="Usa un nombre breve y fácil de reconocer." error={errores.nombre}>
                <input ref={nombreRef} value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Ej. Sopas" maxLength={100} />
              </Field>
              {general && <p className="form-errors">{general}</p>}
              <div className="form-actions">
                <Button className="full" type="submit">{editando ? 'Guardar cambios' : 'Guardar categoría'}</Button>
                {editando && <Button className="full" variant="secondary" type="button" onClick={nueva}>Cancelar edición</Button>}
              </div>
            </form>
          </Panel>
        ) : (
          <Panel title="Solo lectura" subtitle="Tu rol no puede editar las categorías.">
            <p className="field-help">Las categorías las administra el administrador.</p>
          </Panel>
        )}
      </div>
    </>
  )
}

export default Categorias

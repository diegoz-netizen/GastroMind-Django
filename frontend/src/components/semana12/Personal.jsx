import { useRef, useState } from 'react'
import { apiSpring, sesion } from './api'
import { useCargar } from './hooks'
import { Badge, Button, Cargando, Empty, ErrorCarga, Field, Metric, PageTitle, Panel, Search, Toast } from '../../ui'
import { camposDeError, mensajesDeError } from './errores'

const ROLES = [
  { id: 1, nombre: 'Administrador' },
  { id: 4, nombre: 'Mozo' },
  { id: 2, nombre: 'Cocinero' },
  { id: 3, nombre: 'Almacenero' },
]
const FORM_VACIO = { nombreCompleto: '', correo: '', rolId: '', pinAcceso: '' }
const etiquetaRol = (rol) => rol.charAt(0) + rol.slice(1).toLowerCase()
const iniciales = (nombre) => nombre.split(' ').map((x) => x[0]).slice(0, 2).join('').toUpperCase()

// Personal (HU-01, HU-03): lo atiende Spring. El administrador registra empleados y activa o desactiva su acceso.
function Personal() {
  const { datos: empleados, setDatos, cargando, error, recargar } = useCargar(async () => (await apiSpring.get('/empleados')).data)
  const [busqueda, setBusqueda] = useState('')
  const [form, setForm] = useState(FORM_VACIO)
  const [errores, setErrores] = useState({})
  const [general, setGeneral] = useState('')
  const [aviso, setAviso] = useState(null)
  const nombreRef = useRef(null)
  const puedeEscribir = sesion.usuario()?.rol === 'ADMINISTRADOR'

  if (cargando && !empleados) return <Cargando texto="Cargando el personal…" />
  if (error || !empleados) return <ErrorCarga onReintentar={recargar} />

  const activos = empleados.filter((e) => e.estado === 'ACTIVO').length
  const texto = busqueda.trim().toLowerCase()
  const visibles = empleados.filter((e) => `${e.nombreCompleto} ${e.correo}`.toLowerCase().includes(texto))

  function cambiarCampo(evento) {
    setForm({ ...form, [evento.target.name]: evento.target.value })
  }

  async function registrar(evento) {
    evento.preventDefault()
    setErrores({})
    setGeneral('')
    try {
      const r = await apiSpring.post('/empleados', {
        nombreCompleto: form.nombreCompleto.trim(),
        correo: form.correo.trim(),
        rolId: form.rolId ? Number(form.rolId) : null,
        ...(form.pinAcceso ? { pinAcceso: form.pinAcceso } : {}),
      })
      setForm(FORM_VACIO)
      setAviso({ titulo: 'Empleado registrado', texto: r.data.pinAcceso ? `PIN de acceso: ${r.data.pinAcceso}. Solo se muestra ahora.` : 'Recibirá un correo de bienvenida para crear su contraseña.' })
      recargar()
    } catch (err) {
      setErrores(camposDeError(err))
      setGeneral(err.response?.data?.campos ? '' : mensajesDeError(err)[0])
    }
  }

  // PATCH /api/empleados/{id}/estado: activar o desactivar el acceso
  async function cambiarEstado(empleado) {
    const nuevo = empleado.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO'
    setGeneral('')
    try {
      const r = await apiSpring.patch(`/empleados/${empleado.id}/estado`, { estado: nuevo })
      setDatos(empleados.map((e) => (e.id === empleado.id ? r.data : e)))
      setAviso({ titulo: nuevo === 'ACTIVO' ? 'Acceso activado' : 'Acceso desactivado', texto: `${empleado.nombreCompleto} ahora está ${nuevo === 'ACTIVO' ? 'activo' : 'inactivo'}.` })
    } catch (err) {
      setGeneral(mensajesDeError(err)[0])
    }
  }

  return (
    <>
      <PageTitle eyebrow="Equipo" title="Personal" subtitle="Gestiona los accesos y funciones del equipo de la sede."
        action={puedeEscribir && <Button icon="plus" onClick={() => nombreRef.current?.focus()}>Registrar empleado</Button>} />
      {aviso && <Toast titulo={aviso.titulo} texto={aviso.texto} onCerrar={() => setAviso(null)} />}
      <div className="metrics personnel-metrics">
        <Metric label="Personal registrado" value={String(empleados.length)} note="En esta sede" />
        <Metric label="Activos" value={String(activos)} note="Con acceso al sistema" tone="success" />
        <Metric label="Inactivos" value={String(empleados.length - activos)} note="Sin acceso" tone="neutral" />
      </div>
      {general && <p className="form-errors" style={{ marginBottom: 14 }}>{general}</p>}
      <div className="split-layout">
        <section className="content-card">
          <div className="card-toolbar">
            <Search value={busqueda} onChange={setBusqueda} placeholder="Buscar por nombre o correo" />
            <span className="count">{visibles.length} empleados</span>
          </div>
          <div className="table-head staff-grid">
            <span>Empleado</span>
            <span>Rol</span>
            <span>Estado</span>
            <span>Acciones</span>
          </div>
          <div className="item-list">
            {visibles.length ? (
              visibles.map((e, i) => {
                const activo = e.estado === 'ACTIVO'
                return (
                  <article className="list-row staff-grid" key={e.id}>
                    <div className="person">
                      <span className={`avatar avatar-${i % 5}`}>{iniciales(e.nombreCompleto)}</span>
                      <p>
                        <strong>{e.nombreCompleto}</strong>
                        <small>{e.correo}</small>
                      </p>
                    </div>
                    <span className="role">{etiquetaRol(e.rol)}</span>
                    <div>
                      <Badge tone={activo ? 'success' : 'neutral'}>{activo ? 'Activo' : 'Inactivo'}</Badge>
                      {!activo && <small className="login-warning">No puede iniciar sesión</small>}
                    </div>
                    <div className="row-actions">
                      {puedeEscribir && (
                        <Button variant="ghost" icon="power" onClick={() => cambiarEstado(e)}>{activo ? 'Desactivar' : 'Activar'}</Button>
                      )}
                    </div>
                  </article>
                )
              })
            ) : (
              <Empty text="No hay empleados para mostrar." />
            )}
          </div>
        </section>
        {puedeEscribir ? (
          <Panel title="Registrar empleado" subtitle="Crea el acceso para un miembro del equipo.">
            <form onSubmit={registrar} noValidate>
              <Field label="Nombres y apellidos" error={errores.nombreCompleto}>
                <input ref={nombreRef} name="nombreCompleto" value={form.nombreCompleto} onChange={cambiarCampo} placeholder="Ej. Andrea Flores" />
              </Field>
              <Field label="Correo electrónico" error={errores.correo}>
                <input name="correo" type="email" value={form.correo} onChange={cambiarCampo} placeholder="nombre@gastromind.pe" />
              </Field>
              <Field label="Rol" error={errores.rolId}>
                <select name="rolId" value={form.rolId} onChange={cambiarCampo}>
                  <option value="" disabled>Selecciona un rol</option>
                  {ROLES.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
                </select>
              </Field>
              <Field label="PIN de acceso (opcional)" help="4 dígitos para la app del mozo. Si lo dejas vacío, se genera uno." error={errores.pinAcceso}>
                <input name="pinAcceso" inputMode="numeric" maxLength={4} value={form.pinAcceso} onChange={cambiarCampo} placeholder="0000" />
              </Field>
              <Button className="full" type="submit">Registrar empleado</Button>
            </form>
          </Panel>
        ) : (
          <Panel title="Solo lectura" subtitle="Tu rol no puede registrar personal.">
            <p className="field-help">El personal lo administra el administrador.</p>
          </Panel>
        )}
      </div>
    </>
  )
}

export default Personal

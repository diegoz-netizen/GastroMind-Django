import { useEffect, useState } from 'react'
import { sesion } from './components/semana12/api'
import Carta from './components/semana12/Carta'
import Categorias from './components/semana12/Categorias'
import PanelInsumos from './components/semana11/PanelInsumos'
import Login from './components/semana12/Login'
import Pedidos from './components/semana12/Pedidos'
import Personal from './components/semana12/Personal'
import Recetas from './components/semana12/Recetas'
import ListaPractica from './practica/ListaPractica'
import { Icon } from './ui'

// Panel de administración de GastroMind. App elige la pantalla; cada pantalla pide sus datos a la API.
const MENU = [
  { id: 'insumos', etiqueta: 'Insumos', icono: 'box', Pantalla: PanelInsumos },
  { id: 'carta', etiqueta: 'Gestión de carta', icono: 'book', Pantalla: Carta },
  { id: 'categorias', etiqueta: 'Categorías', icono: 'tag', Pantalla: Categorias },
  { id: 'recetas', etiqueta: 'Recetas y costos', icono: 'recipe', Pantalla: Recetas },
  { id: 'pedidos', etiqueta: 'Tomar pedido', icono: 'order', Pantalla: Pedidos },
  { id: 'personal', etiqueta: 'Personal', icono: 'users', Pantalla: Personal },
  { id: 'practica', etiqueta: 'Práctica Lab 12', icono: 'tag', Pantalla: ListaPractica },
]

const iniciales = (nombre) => nombre.split(' ').map((x) => x[0]).slice(0, 2).join('').toUpperCase()
const ROL = { ADMINISTRADOR: 'Administrador', MOZO: 'Mozo', COCINERO: 'Cocinero', ALMACENERO: 'Almacenero' }

function fechaHoy() {
  const texto = new Date().toLocaleDateString('es-PE', { weekday: 'long', day: 'numeric', month: 'long' })
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function App() {
  const [conSesion, setConSesion] = useState(Boolean(sesion.token()))
  const [pagina, setPagina] = useState('insumos')
  const [movil, setMovil] = useState(false)

  useEffect(() => {
    const alCambiar = () => setConSesion(Boolean(sesion.token()))
    window.addEventListener('sesion-cambio', alCambiar)
    return () => window.removeEventListener('sesion-cambio', alCambiar)
  }, [])

  if (!conSesion) {
    return (
      <div className="theme-root theme-light-wine">
        <Login />
      </div>
    )
  }

  const usuario = sesion.usuario() ?? { nombre: 'Usuario', rol: '' }
  const actual = MENU.find((m) => m.id === pagina)
  const Pantalla = actual.Pantalla

  return (
    <div className="app-shell theme-root theme-light-wine">
      <header className="mobile-header">
        <button type="button" className="icon-btn" onClick={() => setMovil(!movil)} aria-label="Abrir menú"><Icon name="menu" /></button>
        <div className="brand compact">
          <span className="brand-mark">G<i /></span>
          <strong>GastroMind</strong>
        </div>
        <span className="mobile-avatar">{iniciales(usuario.nombre)}</span>
      </header>
      <aside className={`sidebar ${movil ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark">G<i /></span>
          <div>
            <strong>GastroMind</strong>
            <span>Administración</span>
          </div>
        </div>
        <nav aria-label="Navegación principal">
          <span className="nav-label">GESTIÓN</span>
          {MENU.map((m) => (
            <button type="button" key={m.id} className={pagina === m.id ? 'active' : ''}
              onClick={() => { setPagina(m.id); setMovil(false) }}>
              <Icon name={m.icono} />
              <span>{m.etiqueta}</span>
              {pagina === m.id && <i />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="venue">
            <span><Icon name="store" /></span>
            <div>
              <small>Restaurante activo</small>
              <strong>Sede Central</strong>
            </div>
          </div>
          <div className="user-mini">
            <span>{iniciales(usuario.nombre)}</span>
            <div>
              <strong>{usuario.nombre}</strong>
              <small>{ROL[usuario.rol] ?? usuario.rol}</small>
            </div>
            <button type="button" aria-label="Cerrar sesión" onClick={sesion.cerrar}><Icon name="logout" /></button>
          </div>
        </div>
      </aside>
      {movil && <button type="button" className="backdrop" onClick={() => setMovil(false)} aria-label="Cerrar menú" />}
      <main className="main-content">
        <div className="top-utility">
          <span>{fechaHoy()}</span>
          <span className="estado-sistema"><i /> Sistema operativo</span>
        </div>
        <Pantalla key={actual.id} />
      </main>
    </div>
  )
}

export default App

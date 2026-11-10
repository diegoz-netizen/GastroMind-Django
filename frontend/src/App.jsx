import { useState } from 'react'
import './App.css'
import Carta from './components/semana09/Carta'
import Personal from './components/semana10/Personal'
import PanelInsumos from './components/semana11/PanelInsumos'

// Panel de administración de GastroMind. App solo elige qué módulo se ve; cada módulo guarda su estado.
// Los componentes están por semana del curso en src/components (semana09, semana10, semana11 y compartido).
// La práctica de la cafetería (Semana 11, Parte 1) sigue en src/practica, pero no se muestra en el panel.
const MODULOS = [
  { id: 'insumos', titulo: 'Insumos', descripcion: 'Stock del almacén, mínimos y altas', icono: 'M4 7h16M4 12h16M4 17h10' },
  { id: 'carta', titulo: 'Carta', descripcion: 'Platillos, recetas y costo de insumos', icono: 'M6 3v18M6 8h4a3 3 0 0 0 0-6H6M14 3v18M18 3c0 6-4 6-4 9' },
  { id: 'personal', titulo: 'Personal', descripcion: 'Empleados por sede y su acceso', icono: 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M2 21a7 7 0 0 1 14 0M17 11a3 3 0 1 0 0-6M22 21a6 6 0 0 0-5-6' },
]

function Icono({ trazo }) {
  return (
    <svg className="icono" viewBox="0 0 24 24" aria-hidden="true">
      <path d={trazo} />
    </svg>
  )
}

function App() {
  const [modulo, setModulo] = useState('insumos')
  const actual = MODULOS.find((item) => item.id === modulo)

  return (
    <div className="admin">
      <aside className="lateral">
        <div className="marca">
          <span className="marca-logo">G</span>
          <div>
            <strong>GastroMind</strong>
            <small>Administración</small>
          </div>
        </div>

        <nav className="menu">
          {MODULOS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === modulo ? 'menu-item activo' : 'menu-item'}
              onClick={() => setModulo(item.id)}
            >
              <Icono trazo={item.icono} />
              {item.titulo}
            </button>
          ))}
        </nav>

        <div className="sede">
          <small>Restaurante</small>
          <strong>Sede Central</strong>
        </div>
      </aside>

      <main className="contenido">
        <header className="cabecera">
          <div>
            <h1>{actual.titulo}</h1>
            <p>{actual.descripcion}</p>
          </div>
        </header>

        {modulo === 'insumos' && <PanelInsumos />}
        {modulo === 'carta' && <Carta />}
        {modulo === 'personal' && <Personal />}
      </main>
    </div>
  )
}

export default App

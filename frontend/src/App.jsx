import { useState } from 'react'
import './App.css'
import Lab10 from './Lab10'
import PanelInsumos from './components/PanelInsumos'
import Practica from './practica/Practica'

// Laboratorio 11: App solo elige qué pantalla se ve. Cada pantalla guarda su propio estado.
// Los insumos del Lab 10 ahora están en la Parte 2 (PanelInsumos), con sus mismos componentes.
const VISTAS = [
  { id: 'practica', titulo: 'Parte 1: práctica (cafetería)' },
  { id: 'panel', titulo: 'Parte 2: panel de insumos' },
  { id: 'lab10', titulo: 'Lab 10: platillos y personal' },
]

function App() {
  const [vista, setVista] = useState('practica')

  return (
    <main className="app">
      <nav className="vistas">
        {VISTAS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={item.id === vista ? 'vista activa' : 'vista'}
            onClick={() => setVista(item.id)}
          >
            {item.titulo}
          </button>
        ))}
      </nav>
      {vista === 'practica' && <Practica />}
      {vista === 'panel' && <PanelInsumos />}
      {vista === 'lab10' && <Lab10 />}
    </main>
  )
}

export default App

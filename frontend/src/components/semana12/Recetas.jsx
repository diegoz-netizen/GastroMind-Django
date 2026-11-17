import { useState } from 'react'
import api from './api'
import { useCargar } from './hooks'
import { Button, Cargando, Empty, ErrorCarga, Miniatura, PageTitle, Search } from '../../ui'

const dinero = (n) => `S/ ${Number(n).toFixed(2)}`
const cantidad = (n) => Number(n).toLocaleString('es-PE', { maximumFractionDigits: 3 })
const LIMITE_COSTO = 35

// Recetas y costos (HU-06, HU-08): el costo sale de la receta y del costo actual de cada insumo
function Recetas() {
  const { datos: productos, cargando, error, recargar } = useCargar(async () => (await api.get('/productos/')).data)
  const [busqueda, setBusqueda] = useState('')

  if (cargando && !productos) return <Cargando texto="Cargando recetas…" />
  if (error || !productos) return <ErrorCarga onReintentar={recargar} />

  const texto = busqueda.trim().toLowerCase()
  const visibles = productos.filter((p) => p.requiere_receta && p.nombre.toLowerCase().includes(texto))

  return (
    <>
      <PageTitle eyebrow="Ingeniería de menú" title="Recetas y costos" subtitle="Conoce el costo real y la rentabilidad de cada preparación."
        action={<Button variant="secondary" icon="refresh" onClick={recargar}>Actualizar costos</Button>} />
      <div className="recipe-toolbar">
        <Search value={busqueda} onChange={setBusqueda} placeholder="Buscar receta" />
        <div className="cost-legend">
          <i />
          Costo recomendado: hasta {LIMITE_COSTO}% del precio
        </div>
      </div>
      {visibles.length ? (
        <div className="recipe-grid">
          {visibles.map((p, i) => {
            const pct = p.porcentaje_costo == null ? null : Math.round(Number(p.porcentaje_costo))
            const excede = pct != null && pct > LIMITE_COSTO
            return (
              <article className="recipe-card" key={p.id}>
                <header>
                  <Miniatura clase={`dish-thumb food-${i % 4}`} nombre={p.nombre} />
                  <div>
                    <span>{p.categoria_nombre}</span>
                    <h2>{p.nombre}</h2>
                  </div>
                </header>
                <div className="recipe-table">
                  <div>
                    <span>Insumo</span>
                    <span>Cantidad</span>
                    <span>Costo</span>
                  </div>
                  {p.detalles_receta.length ? (
                    p.detalles_receta.map((d) => (
                      <div key={d.id}>
                        <strong>{d.ingrediente_nombre}</strong>
                        <span className="numeric">{cantidad(d.cantidad_requerida)} {d.unidad_medida}</span>
                        <span className="numeric">
                          {d.costo_unitario == null ? '—' : dinero(Number(d.cantidad_requerida) * Number(d.costo_unitario))}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div><span>Aún sin receta registrada</span></div>
                  )}
                </div>
                <footer>
                  <div className="cost-summary">
                    <p>
                      <span>Precio de venta</span>
                      <strong>{dinero(p.precio)}</strong>
                    </p>
                    <p>
                      <span>Costo de insumos</span>
                      <strong>{p.costo == null ? '—' : dinero(p.costo)}</strong>
                    </p>
                  </div>
                  {pct != null && (
                    <>
                      <div className="progress-label">
                        <span>Costo sobre el precio</span>
                        <strong className={excede ? 'over' : ''}>{pct}%</strong>
                      </div>
                      <div className="progress">
                        <i className={excede ? 'over' : ''} style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                    </>
                  )}
                </footer>
              </article>
            )
          })}
        </div>
      ) : (
        <div className="content-card"><Empty text="No hay recetas para mostrar." /></div>
      )}
    </>
  )
}

export default Recetas

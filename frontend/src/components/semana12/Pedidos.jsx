import { useState } from 'react'
import api, { apiSpring } from './api'
import { useCargar } from './hooks'
import { Badge, Button, Cargando, Empty, ErrorCarga, Icon, PageTitle, Toast } from '../../ui'
import { mensajesDeError } from './errores'

const dinero = (n) => `S/ ${Number(n).toFixed(2)}`

// Tomar pedido (HU-09): el catálogo sale de la carta; el pedido se envía a Spring con la mesa elegida
function Pedidos() {
  const { datos, cargando, error, recargar } = useCargar(async () => {
    const [productos, categorias, mesas] = await Promise.all([api.get('/productos/'), api.get('/categorias/'), apiSpring.get('/mesas')])
    return { productos: productos.data, categorias: categorias.data, mesas: mesas.data }
  })
  const [categoria, setCategoria] = useState('Todos')
  const [carrito, setCarrito] = useState({})
  const [mesaId, setMesaId] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [aviso, setAviso] = useState(null)
  const [fallo, setFallo] = useState('')

  if (cargando && !datos) return <Cargando texto="Cargando el catálogo…" />
  if (error || !datos) return <ErrorCarga onReintentar={recargar} />
  const { productos, categorias, mesas } = datos

  const visibles = productos.filter((p) => categoria === 'Todos' || p.categoria_nombre === categoria)
  const lineas = productos.filter((p) => carrito[p.id] > 0)
  const unidades = Object.values(carrito).reduce((a, b) => a + b, 0)
  const total = lineas.reduce((suma, p) => suma + carrito[p.id] * Number(p.precio), 0)
  const mesa = mesas.find((m) => String(m.id) === mesaId)

  function cambiar(id, delta) {
    setCarrito((c) => ({ ...c, [id]: Math.max(0, (c[id] || 0) + delta) }))
  }

  // POST /api/pedidos (Spring): mesa libre y al menos un platillo
  async function enviar() {
    setFallo('')
    setEnviando(true)
    try {
      await apiSpring.post('/pedidos', { mesaId: Number(mesaId), items: lineas.map((p) => ({ productoId: p.id, cantidad: carrito[p.id] })) })
      setCarrito({})
      setAviso({ titulo: 'Pedido enviado a cocina', texto: `Mesa ${mesa.numero} · ${unidades} ${unidades === 1 ? 'platillo' : 'platillos'}.` })
      recargar()
    } catch (err) {
      setFallo(mensajesDeError(err)[0])
    }
    setEnviando(false)
  }

  return (
    <>
      <PageTitle eyebrow="Salón" title="Tomar pedido" subtitle={mesa ? `Mesa ${mesa.numero} · ${mesa.zona}, capacidad ${mesa.capacidad}` : 'Elige una mesa y arma el pedido.'}
        action={
          <select className="mesa-select" value={mesaId} onChange={(e) => setMesaId(e.target.value)} aria-label="Mesa">
            <option value="">Elegir mesa…</option>
            {mesas.map((m) => (
              <option key={m.id} value={m.id} disabled={m.estado !== 'LIBRE'}>Mesa {String(m.numero).padStart(2, '0')}{m.estado !== 'LIBRE' ? ' · ocupada' : ''}</option>
            ))}
          </select>
        } />
      {aviso && <Toast titulo={aviso.titulo} texto={aviso.texto} onCerrar={() => setAviso(null)} />}
      <div className="order-layout">
        <section>
          <div className="order-toolbar">
            <h2>Catálogo</h2>
            <div className="segmented">
              {['Todos', ...categorias.map((c) => c.nombre)].map((c) => (
                <button type="button" key={c} className={categoria === c ? 'active' : ''} onClick={() => setCategoria(c)}>{c}</button>
              ))}
            </div>
          </div>
          {visibles.length ? (
            <div className="catalog-grid">
              {visibles.map((p, i) => {
                const disponible = p.estado === 'ACTIVO'
                return (
                  <article className={`catalog-card ${!disponible ? 'unavailable' : ''}`} key={p.id}>
                    <div className={`catalog-visual food-${i % 4}`}>
                      <span>{p.categoria_nombre}</span>
                      {!disponible && <Badge tone="neutral">No disponible</Badge>}
                    </div>
                    <div>
                      <h3>{p.nombre}</h3>
                      <p>{p.categoria_nombre}</p>
                      <footer>
                        <strong>{dinero(p.precio)}</strong>
                        <button type="button" disabled={!disponible} onClick={() => cambiar(p.id, 1)} aria-label={`Añadir ${p.nombre}`}>
                          <Icon name="plus" />
                        </button>
                      </footer>
                    </div>
                  </article>
                )
              })}
            </div>
          ) : (
            <div className="content-card"><Empty text="No hay platillos en esta categoría." /></div>
          )}
        </section>
        <aside className="cart">
          <header>
            <div>
              <span>Pedido de la mesa</span>
              <h2>{mesa ? `Mesa ${String(mesa.numero).padStart(2, '0')}` : 'Sin mesa'}</h2>
            </div>
            <span className="cart-count">{unidades}</span>
          </header>
          <div className="cart-items">
            {lineas.length ? (
              lineas.map((p) => (
                <article key={p.id}>
                  <div>
                    <strong>{p.nombre}</strong>
                    <span>{dinero(p.precio)} c/u</span>
                  </div>
                  <div className="qty">
                    <button type="button" onClick={() => cambiar(p.id, -1)} aria-label={`Quitar uno de ${p.nombre}`}><Icon name="minus" size={15} /></button>
                    <strong>{carrito[p.id]}</strong>
                    <button type="button" onClick={() => cambiar(p.id, 1)} aria-label={`Añadir uno de ${p.nombre}`}><Icon name="plus" size={15} /></button>
                  </div>
                  <strong className="numeric">{dinero(carrito[p.id] * Number(p.precio))}</strong>
                </article>
              ))
            ) : (
              <p className="page-loading">El pedido está vacío.</p>
            )}
          </div>
          <div className="cart-summary">
            <p><span>Subtotal</span><span>{dinero(total)}</span></p>
            <p className="total"><span>Total</span><strong>{dinero(total)}</strong></p>
            {fallo && <p className="form-errors">{fallo}</p>}
            <Button className="full" disabled={!mesaId || !lineas.length || enviando} onClick={enviar}>
              {enviando ? 'Enviando…' : <>Enviar a cocina <Icon name="arrow" /></>}
            </Button>
            <Button variant="ghost" className="full" icon="trash" onClick={() => setCarrito({})}>Vaciar pedido</Button>
          </div>
        </aside>
      </div>
    </>
  )
}

export default Pedidos

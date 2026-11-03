import { useState } from 'react'

// Un insumo (GET /api/catalogo/insumos/). El botón reserva unidades para cocina con un contador propio:
// cada tarjeta guarda el suyo y no se puede reservar más de lo que hay en stock.
function InsumoCard({ nombre, unidad = 'kg', costo, stock, bajoMinimo }) {
  const [reservado, setReservado] = useState(0)
  const stockNumero = Number(stock)
  const agotado = stockNumero === 0

  return (
    <li className="fila">
      <span className="nombre">{nombre}</span>
      <span>S/ {Number(costo).toFixed(2)} por {unidad}</span>
      <span className={agotado ? 'etiqueta agotado' : 'etiqueta'}>
        {agotado ? 'Agotado' : `Stock: ${stockNumero} ${unidad}`}
      </span>
      {bajoMinimo && !agotado && <span className="aviso">¡Últimas unidades!</span>}
      <button type="button" onClick={() => setReservado(reservado + 1)} disabled={reservado >= stockNumero}>
        Reservar 1 {unidad}
      </button>
      {reservado > 0 && <span className="contador">Reservado: {reservado} {unidad}</span>}
    </li>
  )
}

export default InsumoCard

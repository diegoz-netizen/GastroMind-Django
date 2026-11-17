import { useEffect } from 'react'
import { Icon } from '../../ui'

// Mensaje del panel ("Insumo registrado") que se oculta a los 3 segundos, limpiando el temporizador.
function AvisoPanel({ titulo, mensaje, onCerrar }) {
  useEffect(() => {
    const temporizador = setTimeout(() => onCerrar(null), 3000)
    return () => clearTimeout(temporizador)
  }, [mensaje, onCerrar])

  return (
    <div className="toast" role="status">
      <span>
        <Icon name="check" size={17} />
      </span>
      <div>
        <strong>{titulo}</strong>
        <p>{mensaje}</p>
      </div>
      <button type="button" onClick={() => onCerrar(null)} aria-label="Cerrar">
        <Icon name="x" size={16} />
      </button>
    </div>
  )
}

export default AvisoPanel

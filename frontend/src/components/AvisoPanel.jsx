import { useEffect } from 'react'

// Mensaje del panel ("Insumo registrado: ...") que se oculta a los 3 segundos, limpiando el temporizador.
function AvisoPanel({ mensaje, onCerrar }) {
  useEffect(() => {
    const temporizador = setTimeout(() => onCerrar(null), 3000)
    return () => clearTimeout(temporizador)
  }, [mensaje, onCerrar])

  return <p className="aviso-agregado">{mensaje}</p>
}

export default AvisoPanel

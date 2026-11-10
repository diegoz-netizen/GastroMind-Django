import { useEffect } from 'react'

// Muestra "Agregado: <nombre>" y, a los 3 segundos, le pide al padre que lo oculte con onCerrar(null).
// La función que devuelve el efecto limpia el temporizador si llega otro aviso o el componente se desmonta antes.
function Aviso({ mensaje, onCerrar }) {
  useEffect(() => {
    const temporizador = setTimeout(() => onCerrar(null), 3000)
    return () => clearTimeout(temporizador)
  }, [mensaje, onCerrar])

  return <p className="aviso-agregado">{mensaje}</p>
}

export default Aviso

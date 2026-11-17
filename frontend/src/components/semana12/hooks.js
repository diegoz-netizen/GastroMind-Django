import { useCallback, useEffect, useState } from 'react'

// Carga datos al abrir la pantalla y cuando cambian las dependencias.
// Devuelve { datos, setDatos, cargando, error, recargar } para pintar los tres estados: cargando, error y lista.
export function useCargar(funcion, dependencias = []) {
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(false)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let vigente = true
    async function cargar() {
      setCargando(true)
      setError(false)
      try {
        const resultado = await funcion()
        if (vigente) setDatos(resultado)
      } catch (err) {
        console.error(err)
        if (vigente) setError(true)
      }
      if (vigente) setCargando(false)
    }
    cargar()
    return () => {
      vigente = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencias, version])

  const recargar = useCallback(() => setVersion((v) => v + 1), [])
  return { datos, setDatos, cargando, error, recargar }
}

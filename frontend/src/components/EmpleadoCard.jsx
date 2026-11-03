import { useState } from 'react'

// Un empleado (GET /api/empleados de Spring, HU-01 y HU-03). El botón cambia su estado solo en pantalla.
// Al administrador no se le ofrece: no puede desactivarse a sí mismo (HL-008).
function EmpleadoCard({ nombreCompleto, rol, estadoInicial, correo = 'sin correo' }) {
  const [estado, setEstado] = useState(estadoInicial)
  const activo = estado === 'ACTIVO'

  return (
    <li className="fila">
      <span className="nombre">{nombreCompleto}</span>
      <span>{rol}</span>
      <span className="detalle">{correo}</span>
      <span className={activo ? 'etiqueta' : 'etiqueta agotado'}>{activo ? 'Activo' : 'Inactivo'}</span>
      {!activo && <span className="aviso">No puede iniciar sesión</span>}
      <button
        type="button"
        onClick={() => setEstado(activo ? 'INACTIVO' : 'ACTIVO')}
        disabled={rol === 'ADMINISTRADOR'}
      >
        {activo ? 'Desactivar' : 'Activar'}
      </button>
    </li>
  )
}

export default EmpleadoCard

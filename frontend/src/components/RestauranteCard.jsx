import PersonaItem from './PersonaItem'

// Relación 1:N de la Parte 2: un restaurante con su personal. Cada empleado se dibuja con PersonaItem.
function RestauranteCard({ nombre, personal }) {
  const activos = personal.filter((empleado) => empleado.estado === 'ACTIVO').length

  return (
    <article className="tarjeta">
      <h3>{nombre}</h3>
      {personal.length === 0 ? (
        <p className="vacio">Sin empleados registrados</p>
      ) : (
        <ul className="sublista">
          {personal.map((empleado) => (
            <PersonaItem key={empleado.id} nombreCompleto={empleado.nombreCompleto} rol={empleado.rol} />
          ))}
        </ul>
      )}
      <p className="total">
        {personal.length} {personal.length === 1 ? 'empleado' : 'empleados'} · {activos}{' '}
        {activos === 1 ? 'activo' : 'activos'}
      </p>
      {personal.length > 0 && (
        <div className="barra">
          <div className="barra-relleno activos" style={{ width: `${(activos / personal.length) * 100}%` }} />
        </div>
      )}
    </article>
  )
}

export default RestauranteCard

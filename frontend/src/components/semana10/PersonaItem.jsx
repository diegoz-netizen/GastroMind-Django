// Un empleado dentro de la tarjeta de su restaurante
function PersonaItem({ nombreCompleto, rol }) {
  return (
    <li>
      {nombreCompleto} ({rol.toLowerCase()})
    </li>
  )
}

export default PersonaItem

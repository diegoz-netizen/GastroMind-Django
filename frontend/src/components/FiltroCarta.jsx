// Filtro controlado por el padre: el texto y el estado viven en PanelPlatillos.
function FiltroCarta({ texto, estado, onCambiarTexto, onCambiarEstado }) {
  return (
    <div className="filtro">
      <input
        className="buscador"
        type="text"
        placeholder="Buscar platillo..."
        value={texto}
        onChange={(evento) => onCambiarTexto(evento.target.value)}
      />
      <select value={estado} onChange={(evento) => onCambiarEstado(evento.target.value)}>
        <option value="TODOS">Todos</option>
        <option value="ACTIVO">Solo activos</option>
        <option value="INACTIVO">Solo inactivos</option>
      </select>
    </div>
  )
}

export default FiltroCarta

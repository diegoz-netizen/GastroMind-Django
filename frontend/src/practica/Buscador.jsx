// Campo controlado: el texto vive en el padre (valor) y cada tecla se le avisa con onCambiar.
function Buscador({ valor, onCambiar }) {
  return (
    <input
      className="buscador"
      type="text"
      placeholder="Buscar producto..."
      value={valor}
      onChange={(evento) => onCambiar(evento.target.value)}
    />
  )
}

export default Buscador

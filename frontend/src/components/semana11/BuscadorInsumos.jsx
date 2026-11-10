// Lab 11: el buscador que estaba dentro de ListaInsumos (Lab 10), ahora en su propio archivo.
// El texto vive en el padre (valor) y cada tecla se le avisa con onCambiar.
function BuscadorInsumos({ valor, onCambiar }) {
  return (
    <input
      className="buscador"
      type="search"
      placeholder="Buscar insumo por nombre"
      value={valor}
      onChange={(evento) => onCambiar(evento.target.value)}
    />
  )
}

export default BuscadorInsumos

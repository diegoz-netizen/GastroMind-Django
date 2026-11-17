import { Search } from '../../ui'

// Lab 11: el buscador que estaba dentro de ListaInsumos (Lab 10), ahora en su propio archivo.
// El texto vive en el padre (valor) y cada tecla se le avisa con onCambiar.
function BuscadorInsumos({ valor, onCambiar }) {
  return <Search value={valor} onChange={onCambiar} placeholder="Buscar por nombre de insumo" />
}

export default BuscadorInsumos

import { useState } from 'react';

// Un platillo de la carta. El contador es local: cada tarjeta guarda el suyo.
// Un platillo INACTIVO no se puede pedir (la API responde 409 si el mozo lo intenta).
function PlatilloCard({ nombre, precio, categoria = 'Sin categoría', estado, requiereReceta, totalLineas }) {
  const [enPedido, setEnPedido] = useState(0);
  const activo = estado === 'ACTIVO';

  return (
    <article className={activo ? 'platillo' : 'platillo platillo-inactivo'}>
      <div>
        <h3>{nombre}</h3>
        <p className="detalle">{categoria}</p>
        <p className="precio">S/ {Number(precio).toFixed(2)}</p>
        <p className={activo ? 'estado' : 'estado estado-inactivo'}>{activo ? 'Disponible' : 'No disponible'}</p>
        {requiereReceta && totalLineas === 0 && <p className="aviso">Falta cargar su receta (HU-08)</p>}
      </div>
      <div className="acciones">
        <button type="button" onClick={() => setEnPedido(enPedido + 1)} disabled={!activo}>
          Agregar al pedido
        </button>
        {enPedido > 0 && <span className="contador">En el pedido: {enPedido}</span>}
      </div>
    </article>
  );
}

export default PlatilloCard;

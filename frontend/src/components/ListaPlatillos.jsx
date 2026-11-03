import { useState } from 'react';
import PlatilloCard from './PlatilloCard';

const FORM_VACIO = { nombre: '', precio: '', categoria: '' };

// La carta con su buscador y el formulario para agregar un platillo.
// La lista vive en el estado de este componente: todavía no se guarda en Django (eso es la Semana 12).
function ListaPlatillos({ platillos, categorias }) {
  const [lista, setLista] = useState(platillos);
  const [busqueda, setBusqueda] = useState('');
  const [form, setForm] = useState(FORM_VACIO);
  const [error, setError] = useState('');

  const visibles = lista.filter((p) => p.nombre.toLowerCase().includes(busqueda.trim().toLowerCase()));

  function cambiarCampo(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function agregar(e) {
    e.preventDefault();
    const nombre = form.nombre.trim();
    // Mismas reglas que ProductoRecetaSerializer: nombre obligatorio y precio > 0 (min_value 0.01)
    if (!nombre) {
      setError('El nombre es obligatorio.');
      return;
    }
    if (!(Number(form.precio) > 0)) {
      setError('El precio debe ser mayor que 0.');
      return;
    }
    if (!form.categoria) {
      setError('Elija una categoría.');
      return;
    }
    const categoria = categorias.find((c) => c.id === Number(form.categoria));
    const nuevo = {
      id: Math.max(0, ...lista.map((p) => p.id)) + 1,
      nombre,
      precio: Number(form.precio).toFixed(2),
      categoria: categoria.id,
      categoria_nombre: categoria.nombre,
      requiere_receta: true,
      estado: 'ACTIVO', // como en la API: un platillo nace ACTIVO
      detalles_receta: [],
    };
    setLista([...lista, nuevo]);
    setForm(FORM_VACIO);
    setError('');
  }

  return (
    <div>
      <input
        className="buscador"
        type="search"
        placeholder="Buscar platillo por nombre"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />

      {visibles.length === 0 ? (
        <p className="vacio">Ningún platillo coincide con «{busqueda}».</p>
      ) : (
        <div className="grilla">
          {visibles.map((p) => (
            <PlatilloCard
              key={p.id}
              nombre={p.nombre}
              precio={p.precio}
              categoria={p.categoria_nombre}
              estado={p.estado}
              requiereReceta={p.requiere_receta}
              totalLineas={p.detalles_receta.length}
            />
          ))}
        </div>
      )}

      <form className="formulario" onSubmit={agregar} noValidate>
        <h3>Nuevo platillo</h3>
        <label>
          Nombre
          <input name="nombre" value={form.nombre} onChange={cambiarCampo} maxLength={150} />
        </label>
        <label>
          Precio (S/)
          <input name="precio" type="number" step="0.01" value={form.precio} onChange={cambiarCampo} />
        </label>
        <label>
          Categoría
          <select name="categoria" value={form.categoria} onChange={cambiarCampo}>
            <option value="">Elija una</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Agregar a la carta</button>
      </form>
    </div>
  );
}

export default ListaPlatillos;

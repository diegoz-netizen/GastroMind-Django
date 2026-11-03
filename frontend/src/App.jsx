import './App.css';
import { categorias, platillos } from './datos';
import ListaPlatillos from './components/ListaPlatillos';
import RecetaCard from './components/RecetaCard';
import Tarjeta from './components/Tarjeta';

const SEDE = 'Sede Central';

function App() {
  const conReceta = platillos.filter((p) => p.detalles_receta.length > 0);

  return (
    <main className="pagina">
      <header>
        <h1>GastroMind · Administración</h1>
        <p className="detalle">
          {SEDE} · {platillos.length} platillos en la carta
        </p>
      </header>

      <Tarjeta titulo="Carta (HU-06 y HU-07)">
        <ListaPlatillos platillos={platillos} categorias={categorias} />
      </Tarjeta>

      <Tarjeta titulo="Recetas y costo (HU-08)">
        <div className="grilla">
          {conReceta.map((p) => (
            <RecetaCard key={p.id} nombre={p.nombre} precio={p.precio} lineas={p.detalles_receta} />
          ))}
        </div>
      </Tarjeta>
    </main>
  );
}

export default App;

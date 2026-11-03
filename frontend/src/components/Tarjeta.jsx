// Contenedor con título: lo que va entre <Tarjeta> y </Tarjeta> llega como children
// (como un {% block %} que la plantilla hija rellena en Django).
function Tarjeta({ titulo, children }) {
  return (
    <section className="tarjeta">
      <h2 className="tarjeta-titulo">{titulo}</h2>
      {children}
    </section>
  );
}

export default Tarjeta;

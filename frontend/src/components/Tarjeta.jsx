// Contenedor con título: lo que se escribe entre <Tarjeta> y </Tarjeta> llega como children,
// igual que el contenido que una plantilla hija pone dentro de un {% block %} en Django (Semana 6).
function Tarjeta({ titulo, children }) {
  return (
    <section className="seccion">
      <h2>{titulo}</h2>
      {children}
    </section>
  )
}

export default Tarjeta

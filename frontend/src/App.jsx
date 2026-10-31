import './App.css'

// Laboratorio 09: datos escritos a mano, con la misma forma que la respuesta de la API.
// Todavía no se consume la API (eso es en la Semana 12).

// ---------- PARTE 1: catálogo de la Sede Central ----------

// Como GET /api/catalogo/insumos/ (HU-05): los decimales llegan como texto
const insumos = [
  { id: 1, nombre: 'Aceite vegetal', unidad_medida: 'l', costo_unitario: '9.90',
    stock_actual: '6.00', stock_minimo: '4.00', tipo_control: 'RECETA', bajo_stock_minimo: false },
  { id: 2, nombre: 'Pollo', unidad_medida: 'kg', costo_unitario: '11.50',
    stock_actual: '12.00', stock_minimo: '8.00', tipo_control: 'RECETA', bajo_stock_minimo: false },
  { id: 3, nombre: 'Arroz', unidad_medida: 'kg', costo_unitario: '3.80',
    stock_actual: '25.00', stock_minimo: '10.00', tipo_control: 'RECETA', bajo_stock_minimo: false },
  { id: 4, nombre: 'Tomate', unidad_medida: 'kg', costo_unitario: '4.50',
    stock_actual: '2.00', stock_minimo: '5.00', tipo_control: 'RECETA', bajo_stock_minimo: true },
  { id: 7, nombre: 'Cebolla roja', unidad_medida: 'kg', costo_unitario: '3.20',
    stock_actual: '10.00', stock_minimo: '3.00', tipo_control: 'RECETA', bajo_stock_minimo: false },
  { id: 9, nombre: 'Ají amarillo', unidad_medida: 'kg', costo_unitario: '12.00',
    stock_actual: '0.00', stock_minimo: '1.00', tipo_control: 'RECETA', bajo_stock_minimo: true },
]

// Como GET /api/catalogo/productos/ (HU-06 y HU-07): cada platillo trae su receta (relación 1:N)
const platillos = [
  {
    id: 1, nombre: 'Arroz con pollo', precio: '22.00', categoria_nombre: 'Fondos', requiere_receta: true, estado: 'ACTIVO',
    detalles_receta: [
      { id: 1, ingrediente_nombre: 'Arroz', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: 3.8 },
      { id: 2, ingrediente_nombre: 'Pollo', cantidad_requerida: '0.250', unidad_medida: 'kg', costo_unitario: 11.5 },
      { id: 3, ingrediente_nombre: 'Aceite vegetal', cantidad_requerida: '0.020', unidad_medida: 'l', costo_unitario: 9.9 },
      { id: 4, ingrediente_nombre: 'Ají amarillo', cantidad_requerida: '0.030', unidad_medida: 'kg', costo_unitario: 12.0 },
      { id: 5, ingrediente_nombre: 'Cebolla roja', cantidad_requerida: '0.050', unidad_medida: 'kg', costo_unitario: 3.2 },
    ],
  },
  {
    id: 2, nombre: 'Lomo saltado', precio: '32.00', categoria_nombre: 'Fondos', requiere_receta: true, estado: 'ACTIVO',
    detalles_receta: [
      { id: 6, ingrediente_nombre: 'Lomo de res', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: 38.0 },
      { id: 7, ingrediente_nombre: 'Tomate', cantidad_requerida: '0.100', unidad_medida: 'kg', costo_unitario: 4.5 },
      { id: 8, ingrediente_nombre: 'Cebolla roja', cantidad_requerida: '0.080', unidad_medida: 'kg', costo_unitario: 3.2 },
      { id: 9, ingrediente_nombre: 'Papa amarilla', cantidad_requerida: '0.250', unidad_medida: 'kg', costo_unitario: 2.8 },
      { id: 10, ingrediente_nombre: 'Aceite vegetal', cantidad_requerida: '0.030', unidad_medida: 'l', costo_unitario: 9.9 },
      { id: 11, ingrediente_nombre: 'Arroz', cantidad_requerida: '0.150', unidad_medida: 'kg', costo_unitario: 3.8 },
    ],
  },
  {
    id: 3, nombre: 'Chicha morada (jarra)', precio: '12.00', categoria_nombre: 'Bebidas', requiere_receta: false, estado: 'ACTIVO',
    detalles_receta: [],
  },
]

// ---------- PARTE 2: personal (modelos Restaurante y Empleado, registrados en el Admin de Django) ----------

const restaurantes = [
  { id: 1, nombre: 'GastroMind Demo - Sede Central' },
  { id: 2, nombre: 'GastroMind Demo - Sede Norte' },
]

// Como GET /api/empleados (Spring Boot, HU-01 y HU-03)
const empleados = [
  { id: 1, nombreCompleto: 'Administrador Sede Central', rol: 'ADMINISTRADOR', estado: 'ACTIVO',
    correo: 'admin.central@gastromind.demo', restauranteId: 1 },
  { id: 3, nombreCompleto: 'Mozo Demo', rol: 'MOZO', estado: 'ACTIVO',
    correo: 'mozo.demo@gastromind.demo', restauranteId: 1 },
  { id: 4, nombreCompleto: 'Cocinero Demo', rol: 'COCINERO', estado: 'INACTIVO',
    correo: 'cocina.demo@gastromind.demo', restauranteId: 1 },
  { id: 5, nombreCompleto: 'Almacenero Demo', rol: 'ALMACENERO', estado: 'ACTIVO',
    correo: 'almacen.demo@gastromind.demo', restauranteId: 1 },
  { id: 2, nombreCompleto: 'Administrador Sede Norte', rol: 'ADMINISTRADOR', estado: 'ACTIVO',
    correo: 'admin.norte@gastromind.demo', restauranteId: 2 },
]

const nombreApp = 'GastroMind'
const IGV = 0.18

function precioConIgv(precio) {
  return (Number(precio) * (1 + IGV)).toFixed(2)
}

// Costo de insumos de un platillo: suma de cantidad × costo de cada línea de la receta (adelanto de HU-08)
function costoPlatillo(platillo) {
  return platillo.detalles_receta.reduce(
    (total, linea) => total + Number(linea.cantidad_requerida) * Number(linea.costo_unitario),
    0,
  )
}

function App() {
  const sede = 'Sede Central'
  const lomo = platillos[1]

  return (
    <main className="app">
      <header className="encabezado">
        <h1>{nombreApp}: catálogo de la {sede}</h1>
        <p>
          {insumos.length} insumos y {platillos.length} platillos · {lomo.nombre} con IGV: S/ {precioConIgv(lomo.precio)}
        </p>
      </header>

      <section className="seccion">
        <h2>Insumos</h2>
        {insumos.length === 0 ? (
          <p className="vacio">No hay registros</p>
        ) : (
          <ul className="lista">
            {insumos.map((insumo) => (
              <li key={insumo.id} className="fila">
                <span className="nombre">{insumo.nombre}</span>
                <span>S/ {Number(insumo.costo_unitario).toFixed(2)} por {insumo.unidad_medida}</span>
                <span className={Number(insumo.stock_actual) === 0 ? 'etiqueta agotado' : 'etiqueta'}>
                  {Number(insumo.stock_actual) === 0 ? 'Agotado' : `Stock: ${Number(insumo.stock_actual)} ${insumo.unidad_medida}`}
                </span>
                {insumo.bajo_stock_minimo && Number(insumo.stock_actual) > 0 && (
                  <span className="aviso">¡Últimas unidades!</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="seccion">
        <h2>Platillos y su receta</h2>
        <div className="platillos">
          {platillos.map((platillo) => {
            const costo = costoPlatillo(platillo)
            const porcentaje = (costo / Number(platillo.precio)) * 100
            return (
              <article key={platillo.id} className="tarjeta">
                <h3>
                  {platillo.nombre} <small>{platillo.categoria_nombre}</small>
                </h3>
                {platillo.detalles_receta.length === 0 ? (
                  <p className="vacio">No lleva receta</p>
                ) : (
                  <ul className="sublista">
                    {platillo.detalles_receta.map((linea) => (
                      <li key={linea.id}>
                        {linea.ingrediente_nombre}: {Number(linea.cantidad_requerida)} {linea.unidad_medida} × S/{' '}
                        {Number(linea.costo_unitario).toFixed(2)}
                      </li>
                    ))}
                  </ul>
                )}
                <p className="total">
                  Precio S/ {Number(platillo.precio).toFixed(2)} · Costo de insumos S/ {costo.toFixed(2)}
                </p>
                <div className="barra">
                  <div className="barra-relleno" style={{ width: `${porcentaje}%` }} />
                </div>
                <p className="detalle">{porcentaje.toFixed(1)} % del precio se va en insumos</p>
              </article>
            )
          })}
        </div>
      </section>

      <section className="seccion">
        <h2>Restaurantes</h2>
        <ul className="lista">
          {restaurantes.map((restaurante) => (
            <li key={restaurante.id} className="fila">
              <span className="nombre">{restaurante.nombre}</span>
              <span>Código {restaurante.id}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="seccion">
        <h2>Empleados</h2>
        {empleados.length === 0 ? (
          <p className="vacio">No hay registros</p>
        ) : (
          <ul className="lista">
            {empleados.map((empleado) => (
              <li key={empleado.id} className="fila">
                <span className="nombre">{empleado.nombreCompleto}</span>
                <span>{empleado.rol}</span>
                <span className={empleado.estado === 'ACTIVO' ? 'etiqueta' : 'etiqueta agotado'}>
                  {empleado.estado === 'ACTIVO' ? 'Activo' : 'Inactivo'}
                </span>
                {empleado.estado === 'INACTIVO' && <span className="aviso">No puede iniciar sesión</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="seccion">
        <h2>Personal por restaurante</h2>
        {restaurantes.map((restaurante) => {
          const personal = empleados.filter((empleado) => empleado.restauranteId === restaurante.id)
          const activos = personal.filter((empleado) => empleado.estado === 'ACTIVO').length
          return (
            <article key={restaurante.id} className="tarjeta">
              <h3>{restaurante.nombre}</h3>
              {personal.length === 0 ? (
                <p className="vacio">Sin empleados registrados</p>
              ) : (
                <ul className="sublista">
                  {personal.map((empleado) => (
                    <li key={empleado.id}>
                      {empleado.nombreCompleto} ({empleado.rol.toLowerCase()})
                    </li>
                  ))}
                </ul>
              )}
              <p className="total">
                {personal.length} {personal.length === 1 ? 'empleado' : 'empleados'} · {activos}{' '}
                {activos === 1 ? 'activo' : 'activos'}
              </p>
              {personal.length > 0 && (
                <div className="barra">
                  <div className="barra-relleno activos" style={{ width: `${(activos / personal.length) * 100}%` }} />
                </div>
              )}
            </article>
          )
        })}
      </section>
    </main>
  )
}

export default App

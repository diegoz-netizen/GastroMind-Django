// Laboratorio 10: los mismos datos del Laboratorio 09, movidos desde App.jsx (no se crean datos nuevos).
// Tienen la forma de la respuesta de la API; todavía no se consume (eso es en la Semana 12).

// ---------- PARTE 1: catálogo de la Sede Central ----------

// Como GET /api/catalogo/insumos/ (HU-05): los decimales llegan como texto
export const insumos = [
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
export const platillos = [
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

export const restaurantes = [
  { id: 1, nombre: 'Sede Central' },
  { id: 2, nombre: 'Sede Norte' },
]

// Como GET /api/empleados (Spring Boot, HU-01 y HU-03)
export const empleados = [
  { id: 1, nombreCompleto: 'Lucía Fernández', rol: 'ADMINISTRADOR', estado: 'ACTIVO',
    correo: 'lucia.fernandez@gastromind.pe', restauranteId: 1 },
  { id: 3, nombreCompleto: 'Jorge Quispe', rol: 'MOZO', estado: 'ACTIVO',
    correo: 'jorge.quispe@gastromind.pe', restauranteId: 1 },
  { id: 4, nombreCompleto: 'Rosa Huamán', rol: 'COCINERO', estado: 'INACTIVO',
    correo: 'rosa.huaman@gastromind.pe', restauranteId: 1 },
  { id: 5, nombreCompleto: 'Miguel Torres', rol: 'ALMACENERO', estado: 'ACTIVO',
    correo: 'miguel.torres@gastromind.pe', restauranteId: 1 },
  { id: 2, nombreCompleto: 'Andrea Salazar', rol: 'ADMINISTRADOR', estado: 'ACTIVO',
    correo: 'andrea.salazar@gastromind.pe', restauranteId: 2 },
]

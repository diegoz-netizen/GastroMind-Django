// Carta de la Sede Central con la misma forma que GET /api/catalogo/productos/ (ProductoRecetaSerializer).
// Los decimales llegan como texto, igual que en la API. Sale del seed_demo.sql; la Mazamorra morada
// se agregó a mano para tener un platillo que pide receta y todavía no la tiene (HU-08).
// Todavía no se consume la API: eso se hace en la Semana 12.
export const platillos = [
  {
    id: 1,
    nombre: 'Arroz con pollo',
    precio: '22.00',
    categoria: 1,
    categoria_nombre: 'Fondos',
    requiere_receta: true,
    estado: 'ACTIVO',
    detalles_receta: [
      { id: 1, ingrediente_id: 3, ingrediente_nombre: 'Arroz', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: '3.80' },
      { id: 2, ingrediente_id: 2, ingrediente_nombre: 'Pollo', cantidad_requerida: '0.250', unidad_medida: 'kg', costo_unitario: '11.50' },
      { id: 3, ingrediente_id: 1, ingrediente_nombre: 'Aceite vegetal', cantidad_requerida: '0.020', unidad_medida: 'l', costo_unitario: '9.90' },
      { id: 4, ingrediente_id: 9, ingrediente_nombre: 'Ají amarillo', cantidad_requerida: '0.030', unidad_medida: 'kg', costo_unitario: '12.00' },
      { id: 5, ingrediente_id: 7, ingrediente_nombre: 'Cebolla roja', cantidad_requerida: '0.050', unidad_medida: 'kg', costo_unitario: '3.20' },
    ],
  },
  {
    id: 2,
    nombre: 'Lomo saltado',
    precio: '32.00',
    categoria: 1,
    categoria_nombre: 'Fondos',
    requiere_receta: true,
    estado: 'ACTIVO',
    detalles_receta: [
      { id: 6, ingrediente_id: 10, ingrediente_nombre: 'Lomo de res', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: '38.00' },
      { id: 7, ingrediente_id: 4, ingrediente_nombre: 'Tomate', cantidad_requerida: '0.100', unidad_medida: 'kg', costo_unitario: '4.50' },
      { id: 8, ingrediente_id: 7, ingrediente_nombre: 'Cebolla roja', cantidad_requerida: '0.080', unidad_medida: 'kg', costo_unitario: '3.20' },
      { id: 9, ingrediente_id: 8, ingrediente_nombre: 'Papa amarilla', cantidad_requerida: '0.250', unidad_medida: 'kg', costo_unitario: '2.80' },
      { id: 10, ingrediente_id: 1, ingrediente_nombre: 'Aceite vegetal', cantidad_requerida: '0.030', unidad_medida: 'l', costo_unitario: '9.90' },
      { id: 11, ingrediente_id: 3, ingrediente_nombre: 'Arroz', cantidad_requerida: '0.150', unidad_medida: 'kg', costo_unitario: '3.80' },
    ],
  },
  {
    id: 3,
    nombre: 'Chicha morada (jarra)',
    precio: '12.00',
    categoria: 2,
    categoria_nombre: 'Bebidas',
    requiere_receta: false,
    estado: 'ACTIVO',
    detalles_receta: [],
  },
  {
    id: 6,
    nombre: 'Ají de gallina',
    precio: '26.00',
    categoria: 1,
    categoria_nombre: 'Fondos',
    requiere_receta: true,
    estado: 'INACTIVO',
    detalles_receta: [
      { id: 18, ingrediente_id: 2, ingrediente_nombre: 'Pollo', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: '11.50' },
      { id: 19, ingrediente_id: 3, ingrediente_nombre: 'Arroz', cantidad_requerida: '0.150', unidad_medida: 'kg', costo_unitario: '3.80' },
      { id: 20, ingrediente_id: 8, ingrediente_nombre: 'Papa amarilla', cantidad_requerida: '0.200', unidad_medida: 'kg', costo_unitario: '2.80' },
      { id: 21, ingrediente_id: 9, ingrediente_nombre: 'Ají amarillo', cantidad_requerida: '0.040', unidad_medida: 'kg', costo_unitario: '12.00' },
    ],
  },
  {
    id: 7,
    nombre: 'Mazamorra morada',
    precio: '9.00',
    categoria: 6,
    categoria_nombre: 'Postres',
    requiere_receta: true,
    estado: 'ACTIVO',
    detalles_receta: [],
  },
];

// Categorías de la Sede Central (GET /api/catalogo/categorias/), para el formulario
export const categorias = [
  { id: 1, nombre: 'Fondos' },
  { id: 2, nombre: 'Bebidas' },
  { id: 6, nombre: 'Postres' },
];

// Laboratorio 11, Parte 2: la carta de la Sede Central, escrita a mano con la forma de
// GET /api/catalogo/productos/ (HU-07 y HU-08). Los decimales llegan como texto. Todavía no se llama a la API (Semana 12).
export const categorias = [
  { id: 1, nombre: 'Fondos' },
  { id: 2, nombre: 'Entradas' },
  { id: 3, nombre: 'Bebidas' },
  { id: 4, nombre: 'Postres' },
]

export const platillosIniciales = [
  { id: 1, nombre: 'Arroz con pollo', precio: '22.00', categoria: 1, categoria_nombre: 'Fondos',
    requiere_receta: true, estado: 'ACTIVO', costo: '5.08', porcentaje_costo: '23.1' },
  { id: 2, nombre: 'Lomo saltado', precio: '32.00', categoria: 1, categoria_nombre: 'Fondos',
    requiere_receta: true, estado: 'ACTIVO', costo: '10.10', porcentaje_costo: '31.6' },
  { id: 3, nombre: 'Ají de gallina', precio: '24.00', categoria: 1, categoria_nombre: 'Fondos',
    requiere_receta: true, estado: 'ACTIVO', costo: '6.40', porcentaje_costo: '26.7' },
  { id: 4, nombre: 'Papa a la huancaína', precio: '14.00', categoria: 2, categoria_nombre: 'Entradas',
    requiere_receta: true, estado: 'INACTIVO', costo: '3.10', porcentaje_costo: '22.1' },
  { id: 5, nombre: 'Chicha morada (jarra)', precio: '12.00', categoria: 3, categoria_nombre: 'Bebidas',
    requiere_receta: false, estado: 'ACTIVO', costo: '0.00', porcentaje_costo: null },
  { id: 6, nombre: 'Suspiro limeño', precio: '11.00', categoria: 4, categoria_nombre: 'Postres',
    requiere_receta: false, estado: 'INACTIVO', costo: '0.00', porcentaje_costo: null },
]

import { useEffect } from 'react'

// Componentes base del panel, portados del diseño de Figma Make (barra lateral clara + vino).
const trazos = {
  box: (<><path d="m4 7 8-4 8 4-8 4-8-4Z" /><path d="m4 7 8 4 8-4v10l-8 4-8-4V7Z" /><path d="M12 11v10" /></>),
  book: (<><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /><path d="M8 7h8M8 11h6" /></>),
  tag: (<><path d="M20.6 13.6 11 23l-9-9V5h9l9.6 8.6Z" /><circle cx="7" cy="9" r="1.4" /></>),
  recipe: (<><path d="M8 3v4M16 3v4M5 5h14v16H5z" /><path d="M8 11h8M8 15h5" /></>),
  order: (<><path d="M4 3h2l2 13h10l2-8H7" /><circle cx="10" cy="20" r="1" /><circle cx="17" cy="20" r="1" /></>),
  users: (<><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></>),
  search: (<><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>),
  plus: <path d="M12 5v14M5 12h14" />,
  edit: (<><path d="m4 20 4.2-1 10.7-10.7-3.2-3.2L5 15.8 4 20Z" /><path d="m14.5 6.5 3 3" /></>),
  trash: <path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6" />,
  power: (<><path d="M12 2v10" /><path d="M18.4 5.6a9 9 0 1 1-12.8 0" /></>),
  store: (<><path d="M3 10h18l-2-6H5l-2 6Z" /><path d="M5 10v10h14V10M9 20v-6h6v6" /><path d="M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" /></>),
  chevron: <path d="m9 18 6-6-6-6" />,
  x: <path d="m6 6 12 12M18 6 6 18" />,
  check: <path d="m5 12 4 4L19 6" />,
  alert: (<><path d="M12 3 2.5 20h19L12 3Z" /><path d="M12 9v5M12 17.5v.5" /></>),
  eye: (<><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" /><circle cx="12" cy="12" r="2.5" /></>),
  eyeOff: (<><path d="m3 3 18 18M10.6 6.2c.45-.13.92-.2 1.4-.2 6.5 0 10 6 10 6a18 18 0 0 1-2.1 2.8M6.2 6.2A17 17 0 0 0 2 12s3.5 6 10 6c1 0 1.9-.14 2.7-.4" /></>),
  logout: (<><path d="M10 17l5-5-5-5M15 12H3" /><path d="M14 3h7v18h-7" /></>),
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  refresh: (<><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M6.1 8a7 7 0 0 1 11.8-2L20 8M4 16l2.1 2a7 7 0 0 0 11.8-2" /></>),
  mail: (<><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></>),
  lock: (<><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>),
  arrow: <path d="M5 12h14M14 7l5 5-5 5" />,
  minus: <path d="M5 12h14" />,
  camera: (<><path d="M3 8h4l2-3h6l2 3h4v11H3z" /><circle cx="12" cy="13" r="3.5" /></>),
}

export function Icon({ name, size = 18 }) {
  return (
    <svg aria-hidden="true" className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {trazos[name]}
    </svg>
  )
}

export function Button({ children, variant = 'primary', icon, className = '', ...props }) {
  return (
    <button className={`btn btn-${variant} ${className}`} {...props}>
      {icon && <Icon name={icon} size={17} />}
      <span>{children}</span>
    </button>
  )
}

export function Field({ label, help, error, children }) {
  return (
    <label className={`field ${error ? 'field-error' : ''}`}>
      <span className="field-label">{label}</span>
      {children}
      {help && !error && <span className="field-help">{help}</span>}
      {error && (
        <span className="field-error-text">
          <Icon name="alert" size={14} />
          {error}
        </span>
      )}
    </label>
  )
}

export function Badge({ tone, children }) {
  return (
    <span className={`badge badge-${tone}`}>
      <i />
      {children}
    </span>
  )
}

export function Search({ value, onChange, placeholder }) {
  return (
    <label className="search">
      <Icon name="search" size={19} />
      <span className="sr-only">Buscar</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
      {value && (
        <button type="button" onClick={() => onChange('')} aria-label="Limpiar búsqueda">
          <Icon name="x" size={16} />
        </button>
      )}
    </label>
  )
}

export function Metric({ label, value, note, tone = 'default' }) {
  return (
    <article className={`metric metric-${tone}`}>
      <div className="metric-top">
        <span>{label}</span>
        <i />
      </div>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </article>
  )
}

export function PageTitle({ eyebrow, title, subtitle, action }) {
  return (
    <header className="page-title">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </header>
  )
}

export function Panel({ title, subtitle, children }) {
  return (
    <aside className="form-panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      {children}
    </aside>
  )
}

export function Empty({ text, detail = 'Prueba con otro término o limpia los filtros aplicados.' }) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name="search" size={24} />
      </span>
      <h3>{text}</h3>
      <p>{detail}</p>
    </div>
  )
}

export function Cargando({ texto = 'Cargando…' }) {
  return <div className="page-loading">{texto}</div>
}

export function ErrorCarga({ onReintentar }) {
  return (
    <div className="connection-error">
      <span>
        <Icon name="alert" size={27} />
      </span>
      <h2>No pudimos cargar la información</h2>
      <p>Revisa tu conexión e inténtalo nuevamente.</p>
      <Button variant="secondary" icon="refresh" onClick={onReintentar}>
        Reintentar
      </Button>
    </div>
  )
}

// Aviso de éxito arriba a la derecha; se cierra solo a los 3 segundos
export function Toast({ titulo, texto, onCerrar }) {
  useEffect(() => {
    const temporizador = setTimeout(onCerrar, 3500)
    return () => clearTimeout(temporizador)
  }, [titulo, texto, onCerrar])

  return (
    <div className="toast" role="status">
      <span>
        <Icon name="check" size={17} />
      </span>
      <div>
        <strong>{titulo}</strong>
        {texto && <p>{texto}</p>}
      </div>
      <button type="button" onClick={onCerrar} aria-label="Cerrar">
        <Icon name="x" size={16} />
      </button>
    </div>
  )
}

// Recuadro del platillo o insumo: su ícono o la inicial del nombre
export function Miniatura({ nombre, icono, clase }) {
  return (
    <span className={clase}>
      {icono ?? nombre.slice(0, 1)}
    </span>
  )
}

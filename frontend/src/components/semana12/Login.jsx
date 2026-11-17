import { useState } from 'react'
import { iniciarSesion } from './api'
import { Button, Field, Icon } from '../../ui'
import { mensajesDeError } from './errores'

// Inicio de sesión: el login lo hace Spring; Django valida el mismo token
function Login() {
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [ver, setVer] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function enviar(evento) {
    evento.preventDefault()
    setError('')
    setCargando(true)
    try {
      await iniciarSesion(correo, password)
    } catch (err) {
      setError(err.response?.status === 401 || err.response?.status === 403 ? 'Correo o contraseña incorrectos.' : mensajesDeError(err)[0])
    }
    setCargando(false)
  }

  return (
    <main className="login-page">
      <div className="login-brand">
        <span className="brand-mark large">G<i /></span>
        <div>
          <strong>GastroMind</strong>
          <span>Administración</span>
        </div>
      </div>
      <section className="login-card">
        <div className="login-welcome">
          <span>Acceso seguro</span>
          <h1>Bienvenido de vuelta</h1>
          <p>Ingresa tus credenciales para gestionar la sede.</p>
        </div>
        <form onSubmit={enviar}>
          <Field label="Correo electrónico">
            <div className="input-icon">
              <Icon name="mail" />
              <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} autoComplete="username" placeholder="nombre@gastromind.pe" required />
            </div>
          </Field>
          <Field label="Contraseña">
            <div className="input-icon password">
              <Icon name="lock" />
              <input type={ver ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
              <button type="button" onClick={() => setVer(!ver)} aria-label="Mostrar contraseña"><Icon name={ver ? 'eyeOff' : 'eye'} /></button>
            </div>
          </Field>
          {error && <p className="login-error"><Icon name="alert" size={16} />{error}</p>}
          <Button className="full login-button" disabled={cargando}>
            {cargando ? <><span className="spinner" />Ingresando…</> : 'Ingresar al sistema'}
          </Button>
        </form>
      </section>
      <p className="login-foot">GastroMind · Panel de administración</p>
    </main>
  )
}

export default Login

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles.css'
import App from './App'

function AuthWrapper() {
  const token = localStorage.getItem('auth_token')
  const isLoginPage = window.location.pathname === '/login'
  if (!token && !isLoginPage) {
    window.location.replace('/login')
    return null
  }
  return <App />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthWrapper />
  </StrictMode>,
)

import { useState } from 'react'
import { AuthShell } from './AuthShell'
import { ForgotPasswordForm } from './ForgotPasswordForm'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

type AuthMode = 'login' | 'register' | 'forgot-password'

export function LoginPage() {
  const [mode, setMode] = useState<AuthMode>('login')

  return (
    <AuthShell>
      <div key={mode} className="animate-fade-in-up">
        {mode === 'login' && (
          <LoginForm
            onSwitchToRegister={() => setMode('register')}
            onForgotPassword={() => setMode('forgot-password')}
          />
        )}
        {mode === 'register' && <RegisterForm onSwitchToLogin={() => setMode('login')} />}
        {mode === 'forgot-password' && (
          <ForgotPasswordForm onBackToLogin={() => setMode('login')} />
        )}
      </div>
    </AuthShell>
  )
}

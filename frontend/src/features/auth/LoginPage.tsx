import { useState } from 'react'
import { AuthShell } from './AuthShell'
import { ForgotPasswordForm } from './ForgotPasswordForm'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

type AuthMode = 'login' | 'register' | 'forgot-password'

interface LoginPageProps {
  redirectTo?: string | null
  emailConvite?: string
  modoInicial?: AuthMode
}

export function LoginPage({
  redirectTo = null,
  emailConvite,
  modoInicial = 'login',
}: LoginPageProps) {
  const [mode, setMode] = useState<AuthMode>(modoInicial)

  return (
    <AuthShell>
      <div key={mode} className="animate-fade-in-up">
        {mode === 'login' && (
          <LoginForm
            redirectTo={redirectTo}
            onSwitchToRegister={() => setMode('register')}
            onForgotPassword={() => setMode('forgot-password')}
          />
        )}
        {mode === 'register' && (
          <RegisterForm
            redirectTo={redirectTo}
            emailTravado={emailConvite}
            onSwitchToLogin={() => setMode('login')}
          />
        )}
        {mode === 'forgot-password' && (
          <ForgotPasswordForm onBackToLogin={() => setMode('login')} />
        )}
      </div>
    </AuthShell>
  )
}

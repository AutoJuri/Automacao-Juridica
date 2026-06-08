import { useState } from 'react'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'
import { AuthVisualPanel } from './AuthVisualPanel'
import { Scale } from 'lucide-react'

type AuthMode = 'login' | 'register'

export function LoginPage() {
  const [mode, setMode] = useState<AuthMode>('login')

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left panel — forms (50%) */}
      <div className="relative flex w-full lg:w-1/2 min-h-screen">
        {/* Logo — canto superior esquerdo */}
        <div className="absolute top-0 left-0 z-10 flex items-center gap-2.5 px-8 sm:px-14 pt-10">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#3B5BDB]">
            <Scale className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="text-sm font-semibold text-[#111827] tracking-tight">AdvogAtiva</span>
            <span className="block text-[10px] text-[#6B7280] tracking-[0.15em] uppercase leading-none mt-0.5">
              Secure Hub
            </span>
          </div>
        </div>

        {/* Formulário — centralizado vertical e horizontalmente */}
        <div className="flex flex-1 items-center justify-center px-8 sm:px-14 py-24">
          <div className="w-full max-w-sm">
            <div key={mode} className="animate-fade-in-up">
              {mode === 'login' ? (
                <LoginForm onSwitchToRegister={() => setMode('register')} />
              ) : (
                <RegisterForm onSwitchToLogin={() => setMode('login')} />
              )}
            </div>
          </div>
        </div>

        {/* Footer — canto inferior */}
        <p className="absolute bottom-0 left-0 right-0 pb-8 text-center text-[10px] text-[#9CA3AF] tracking-wide">
          © 2026 AdvogAtiva. Dados protegidos com criptografia AES-256.
        </p>
      </div>

      {/* Right panel — visual (50%) */}
      <AuthVisualPanel />
    </div>
  )
}

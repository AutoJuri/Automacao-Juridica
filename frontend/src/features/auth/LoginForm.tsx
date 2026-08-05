import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Eye, EyeOff, Mail, Lock } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { useAuthStore } from '#/store/auth.store'

interface LoginFormProps {
  onSwitchToRegister: () => void
}

export function LoginForm({ onSwitchToRegister }: LoginFormProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // Mock: define auth em memória e redireciona — sem chamada real de API
    setAuth('mock-access-token-15min', {
      id: '1',
      name: 'João Advogado',
      email: email || 'joao@advocacia.com',
    })
    navigate({ to: '/' })
  }

  return (
    <div className="animate-fade-in-up">
      <div className="mb-8">
        <h1
          className="text-[2.1rem] leading-tight text-[#111827]"
          style={{ fontFamily: 'DM Serif Display, Georgia, serif' }}
        >
          Bem-vindo de volta
        </h1>
        <p className="mt-2 text-sm text-[#6B7280]">
          Acesse seu painel de acompanhamento de processos.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="login-email" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            E-mail
          </Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="login-email"
              type="email"
              autoComplete="email"
              placeholder="seu@email.com.br"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="login-password" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            Senha
          </Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pl-10 pr-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
              aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              className="text-xs text-[#3B5BDB] hover:text-[#2d4cba] transition-colors mt-1"
            >
              Esqueci minha senha
            </button>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md"
        >
          Entrar na plataforma
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-[#6B7280]">
        Não tem conta?{' '}
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="text-[#3B5BDB] hover:text-[#2d4cba] font-medium transition-colors"
        >
          Cadastre-se gratuitamente
        </button>
      </p>
    </div>
  )
}

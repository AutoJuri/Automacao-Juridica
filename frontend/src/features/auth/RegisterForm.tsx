import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Eye, EyeOff, Mail, Lock, User } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { useAuthStore } from '#/store/auth.store'

interface RegisterFormProps {
  onSwitchToLogin: () => void
}

export function RegisterForm({ onSwitchToLogin }: RegisterFormProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // Mock: define auth em memória e redireciona — sem chamada real de API
    setAuth('mock-access-token-15min', {
      id: '1',
      name: name || 'Novo Advogado',
      email: email || 'novo@advocacia.com',
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
          Criar sua conta
        </h1>
        <p className="mt-2 text-sm text-[#6B7280]">
          Comece a monitorar seus processos de forma automática.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="reg-name" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            Nome completo
          </Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reg-name"
              type="text"
              autoComplete="name"
              placeholder="Dr. João da Silva"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="pl-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="reg-email" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            E-mail profissional
          </Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reg-email"
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
          <Label htmlFor="reg-password" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            Senha
          </Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reg-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Mínimo 8 caracteres"
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
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="reg-confirm" className="text-xs font-medium text-[#374151] uppercase tracking-wide">
            Confirmar senha
          </Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reg-confirm"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Repita a senha"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="pl-10 pr-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
              aria-label={showConfirm ? 'Ocultar confirmação' : 'Mostrar confirmação'}
            >
              {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md mt-2"
        >
          Criar conta gratuitamente
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-[#6B7280]">
        Já tem conta?{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-[#3B5BDB] hover:text-[#2d4cba] font-medium transition-colors"
        >
          Entrar
        </button>
      </p>
    </div>
  )
}

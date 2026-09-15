import { useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { Eye, EyeOff, Loader2, Mail, Lock } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { useAuthStore } from '#/store/auth.store'
import { login } from './auth.api'
import { MUITAS_TENTATIVAS, mensagemDeErro } from './auth.errors'
import { loginSchema, type LoginFormValues } from './auth.schemas'
import { FieldError, FormError } from './AuthFormFeedback'

interface LoginFormProps {
  onSwitchToRegister: () => void
  onForgotPassword: () => void
}

export function LoginForm({ onSwitchToRegister, onForgotPassword }: LoginFormProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) })

  const entrar = useMutation({
    mutationFn: login,
    onSuccess: ({ access_token, user }) => {
      setAuth(access_token, user)
      navigate({ to: '/' })
    },
  })

  const erroApi = entrar.error
    ? mensagemDeErro(entrar.error, {
        401: 'E-mail ou senha inválidos.',
        429: MUITAS_TENTATIVAS,
      })
    : null

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

      <form onSubmit={handleSubmit((valores) => entrar.mutate(valores))} className="space-y-5" noValidate>
        <FormError message={erroApi} />

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
              aria-invalid={errors.email !== undefined}
              {...register('email')}
              className="pl-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
          </div>
          <FieldError message={errors.email?.message} />
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
              aria-invalid={errors.password !== undefined}
              {...register('password')}
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
          <FieldError message={errors.password?.message} />
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onForgotPassword}
              className="text-xs text-[#3B5BDB] hover:text-[#2d4cba] transition-colors mt-1"
            >
              Esqueci minha senha
            </button>
          </div>
        </div>

        <Button
          type="submit"
          disabled={entrar.isPending}
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-70"
        >
          {entrar.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Entrando...
            </>
          ) : (
            'Entrar na plataforma'
          )}
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

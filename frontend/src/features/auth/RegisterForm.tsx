import { useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { Eye, EyeOff, Loader2, Mail, Lock, User } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { useAuthStore } from '#/store/auth.store'
import { cadastrar } from './auth.api'
import { MUITAS_TENTATIVAS, mensagemDeErro } from './auth.errors'
import { registerSchema, type RegisterFormValues } from './auth.schemas'
import { FieldError, FormError } from './AuthFormFeedback'

interface RegisterFormProps {
  onSwitchToLogin: () => void
}

export function RegisterForm({ onSwitchToLogin }: RegisterFormProps) {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) })

  const criarConta = useMutation({
    // O backend já emite a sessão no cadastro, então não há login extra aqui.
    mutationFn: cadastrar,
    onSuccess: ({ access_token, user }) => {
      setAuth(access_token, user)
      navigate({ to: '/' })
    },
  })

  const erroApi = criarConta.error
    ? mensagemDeErro(criarConta.error, {
        409: 'Este e-mail já está cadastrado. Tente entrar na sua conta.',
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
          Criar sua conta
        </h1>
        <p className="mt-2 text-sm text-[#6B7280]">
          Comece a monitorar seus processos de forma automática.
        </p>
      </div>

      <form
        onSubmit={handleSubmit(({ name, email, password }) =>
          criarConta.mutate({ name, email, password }),
        )}
        className="space-y-4"
        noValidate
      >
        <FormError message={erroApi} />

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
              aria-invalid={errors.name !== undefined}
              {...register('name')}
              className="pl-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
          </div>
          <FieldError message={errors.name?.message} />
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
              aria-invalid={errors.email !== undefined}
              {...register('email')}
              className="pl-10 h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
          </div>
          <FieldError message={errors.email?.message} />
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
              aria-invalid={errors.confirm !== undefined}
              {...register('confirm')}
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
          <FieldError message={errors.confirm?.message} />
        </div>

        <Button
          type="submit"
          disabled={criarConta.isPending}
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md mt-2 disabled:opacity-70"
        >
          {criarConta.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Criando conta...
            </>
          ) : (
            'Criar conta gratuitamente'
          )}
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

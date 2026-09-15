import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { ArrowLeft, Loader2, Mail } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { recuperarSenha } from './auth.api'
import { MUITAS_TENTATIVAS, mensagemDeErro } from './auth.errors'
import { forgotPasswordSchema, type ForgotPasswordFormValues } from './auth.schemas'
import { FieldError, FormError, FormSuccess } from './AuthFormFeedback'

interface ForgotPasswordFormProps {
  onBackToLogin: () => void
}

export function ForgotPasswordForm({ onBackToLogin }: ForgotPasswordFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) })

  const pedirLink = useMutation({
    mutationFn: ({ email }: ForgotPasswordFormValues) => recuperarSenha(email),
  })

  const erroApi = pedirLink.error
    ? mensagemDeErro(pedirLink.error, { 429: MUITAS_TENTATIVAS })
    : null

  return (
    <div className="animate-fade-in-up">
      <div className="mb-8">
        <h1
          className="text-[2.1rem] leading-tight text-[#111827]"
          style={{ fontFamily: 'DM Serif Display, Georgia, serif' }}
        >
          Recuperar senha
        </h1>
        <p className="mt-2 text-sm text-[#6B7280]">
          Informe seu e-mail e enviaremos um link para você definir uma nova senha.
        </p>
      </div>

      {/* A mensagem é a mesma do backend, que não revela se o e-mail existe. */}
      {pedirLink.isSuccess ? (
        <div className="space-y-5">
          <FormSuccess message={pedirLink.data.message} />
          <p className="text-xs leading-relaxed text-[#6B7280]">
            O link vale por 1 hora. Se não chegar, verifique o endereço informado e tente
            novamente.
          </p>
          <Button
            type="button"
            onClick={onBackToLogin}
            className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide"
          >
            Voltar para o login
          </Button>
        </div>
      ) : (
        <>
          <form
            onSubmit={handleSubmit((valores) => pedirLink.mutate(valores))}
            className="space-y-5"
            noValidate
          >
            <FormError message={erroApi} />

            <div className="space-y-1.5">
              <Label
                htmlFor="forgot-email"
                className="text-xs font-medium text-[#374151] uppercase tracking-wide"
              >
                E-mail
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
                <Input
                  id="forgot-email"
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

            <Button
              type="submit"
              disabled={pedirLink.isPending}
              className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-70"
            >
              {pedirLink.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Enviando...
                </>
              ) : (
                'Enviar link de recuperação'
              )}
            </Button>
          </form>

          <button
            type="button"
            onClick={onBackToLogin}
            className="mt-6 flex w-full items-center justify-center gap-1.5 text-sm text-[#6B7280] hover:text-[#111827] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Voltar para o login
          </button>
        </>
      )}
    </div>
  )
}

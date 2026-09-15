import { useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Eye, EyeOff, Loader2, Lock } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { useAuthStore } from '#/store/auth.store'
import { redefinirSenha } from './auth.api'
import { MUITAS_TENTATIVAS, mensagemDeErro } from './auth.errors'
import { resetPasswordSchema, type ResetPasswordFormValues } from './auth.schemas'
import { FieldError, FormError, FormSuccess } from './AuthFormFeedback'

const TITULO_CSS = 'text-[2.1rem] leading-tight text-[#111827]'
const TITULO_FONTE = { fontFamily: 'DM Serif Display, Georgia, serif' }

export function ResetPasswordForm({ token }: { token: string }) {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) })

  const redefinir = useMutation({
    mutationFn: ({ password }: ResetPasswordFormValues) => redefinirSenha(token, password),
    // A senha trocou: qualquer access token ainda em memória pertence à sessão
    // antiga e não pode continuar autenticando, senão "Entrar com a nova senha"
    // cairia direto no painel (requireGuest vê isAuthenticated e nem chega ao login).
    onSuccess: () => {
      useAuthStore.getState().clearAuth()
    },
  })

  if (!token) {
    return <LinkInvalido descricao="Este link de recuperação está incompleto." />
  }

  if (redefinir.isSuccess) {
    return (
      <div className="animate-fade-in-up space-y-5">
        <h1 className={TITULO_CSS} style={TITULO_FONTE}>
          Senha redefinida
        </h1>
        <FormSuccess message={redefinir.data.message} />
        <p className="text-xs leading-relaxed text-[#6B7280]">
          Por segurança, as sessões abertas em outros dispositivos foram encerradas.
        </p>
        <Button
          asChild
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide"
        >
          <Link to="/login">Entrar com a nova senha</Link>
        </Button>
      </div>
    )
  }

  const erroApi = redefinir.error
    ? mensagemDeErro(redefinir.error, {
        400: 'Este link é inválido ou já expirou. Solicite um novo na tela de login.',
        429: MUITAS_TENTATIVAS,
      })
    : null

  return (
    <div className="animate-fade-in-up">
      <div className="mb-8">
        <h1 className={TITULO_CSS} style={TITULO_FONTE}>
          Definir nova senha
        </h1>
        <p className="mt-2 text-sm text-[#6B7280]">
          Escolha uma senha nova para voltar a acessar seu painel.
        </p>
      </div>

      <form
        onSubmit={handleSubmit((valores) => redefinir.mutate(valores))}
        className="space-y-4"
        noValidate
      >
        <FormError message={erroApi} />

        <div className="space-y-1.5">
          <Label
            htmlFor="reset-password"
            className="text-xs font-medium text-[#374151] uppercase tracking-wide"
          >
            Nova senha
          </Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reset-password"
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
          <Label
            htmlFor="reset-confirm"
            className="text-xs font-medium text-[#374151] uppercase tracking-wide"
          >
            Confirmar nova senha
          </Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              id="reset-confirm"
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
          disabled={redefinir.isPending}
          className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide transition-all duration-200 shadow-sm hover:shadow-md mt-2 disabled:opacity-70"
        >
          {redefinir.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Salvando...
            </>
          ) : (
            'Salvar nova senha'
          )}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-[#6B7280]">
        <Link to="/login" className="text-[#3B5BDB] hover:text-[#2d4cba] font-medium transition-colors">
          Voltar para o login
        </Link>
      </p>
    </div>
  )
}

function LinkInvalido({ descricao }: { descricao: string }) {
  return (
    <div className="animate-fade-in-up space-y-5">
      <h1 className={TITULO_CSS} style={TITULO_FONTE}>
        Link inválido
      </h1>
      <p className="text-sm text-[#6B7280]">
        {descricao} Solicite um novo link em &ldquo;Esqueci minha senha&rdquo;.
      </p>
      <Button
        asChild
        className="w-full h-11 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm tracking-wide"
      >
        <Link to="/login">Ir para o login</Link>
      </Button>
    </div>
  )
}

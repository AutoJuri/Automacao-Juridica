/**
 * Schemas de validação dos formulários de autenticação.
 *
 * Nota: validação de frontend é só UX. O backend revalida tudo com Pydantic —
 * os limites aqui apenas espelham os de backend/app/schemas/auth.py.
 */

import { z } from 'zod'

import { cabeEmBytesDoBcrypt, SENHA_MAX, SENHA_MIN } from '#/lib/password-validation'

const email = z
  .string()
  .trim()
  .min(1, 'Informe seu e-mail')
  .max(255, 'E-mail muito longo')
  .pipe(z.email('E-mail inválido'))

const novaSenha = z
  .string()
  .min(SENHA_MIN, `A senha precisa de no mínimo ${SENHA_MIN} caracteres`)
  .max(SENHA_MAX, `A senha pode ter no máximo ${SENHA_MAX} caracteres`)
  .refine(cabeEmBytesDoBcrypt, `A senha excede o limite de ${SENHA_MAX} bytes`)

export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Informe sua senha').max(SENHA_MAX, 'Senha inválida'),
})

export const registerSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(2, 'Informe seu nome completo')
      .max(255, 'Nome muito longo'),
    email,
    password: novaSenha,
    confirm: z.string().min(1, 'Confirme sua senha'),
  })
  .refine((dados) => dados.password === dados.confirm, {
    message: 'As senhas não coincidem',
    path: ['confirm'],
  })

export const forgotPasswordSchema = z.object({ email })

export const resetPasswordSchema = z
  .object({
    password: novaSenha,
    confirm: z.string().min(1, 'Confirme sua senha'),
  })
  .refine((dados) => dados.password === dados.confirm, {
    message: 'As senhas não coincidem',
    path: ['confirm'],
  })

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

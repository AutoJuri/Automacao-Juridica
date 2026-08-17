/**
 * Schemas de validação do formulário de credenciais do e-SAJ.
 *
 * Nota: validação de frontend é só UX. O backend revalida tudo com Pydantic
 * (incluindo o checksum do CPF de novo) — o objetivo aqui é só dar feedback
 * imediato sem gastar uma chamada de API com um CPF obviamente inválido.
 */

import { z } from 'zod'

import { cabeEmBytesDoBcrypt, SENHA_MAX, SENHA_MIN } from '#/lib/password-validation'

const CPF_DIGITOS = 11

function normalizeCpf(cpf: string): string {
  return cpf.replace(/\D/g, '')
}

/** Mesmo algoritmo de dígito verificador do backend (app/core/cpf.py). */
function isValidCpf(cpf: string): boolean {
  if (cpf.length !== CPF_DIGITOS || !/^\d+$/.test(cpf)) {
    return false
  }
  if (cpf === cpf[0]?.repeat(CPF_DIGITOS)) {
    return false
  }

  const digitos = cpf.split('').map(Number)

  const digitoVerificador = (fatia: number[]) => {
    const pesoInicial = fatia.length + 1
    const soma = fatia.reduce((acc, digito, indice) => acc + digito * (pesoInicial - indice), 0)
    const resto = soma % 11
    return resto < 2 ? 0 : 11 - resto
  }

  if (digitoVerificador(digitos.slice(0, 9)) !== digitos[9]) {
    return false
  }
  return digitoVerificador(digitos.slice(0, 10)) === digitos[10]
}

export const esajCredentialSchema = z.object({
  cpf: z
    .string()
    .trim()
    .min(1, 'Informe o CPF')
    .transform(normalizeCpf)
    .refine((cpf) => isValidCpf(cpf), 'CPF inválido'),
  senha: z
    .string()
    .min(SENHA_MIN, `A senha precisa de no mínimo ${SENHA_MIN} caracteres`)
    .max(SENHA_MAX, `A senha pode ter no máximo ${SENHA_MAX} caracteres`)
    .refine(cabeEmBytesDoBcrypt, `A senha excede o limite de ${SENHA_MAX} bytes`),
})

export type EsajCredentialFormValues = z.infer<typeof esajCredentialSchema>

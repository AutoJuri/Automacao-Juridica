import { z } from 'zod'

import { modelosPeca } from './elaboracao.mock'
import type { RascunhoManual } from './elaboracoes.types'

const pecas = new Set(modelosPeca.map((item) => item.id))

const opcional = z.string().trim().max(255, 'Texto muito longo')

export const novaElaboracaoSchema = z.object({
  peca: z.string().refine((valor) => pecas.has(valor), 'Escolha a peça'),
  titulo: z.string().trim().min(1, 'Informe um título').max(120, 'Título muito longo'),
  nu_processo: z.string().trim().max(50, 'Número muito longo'),
  parte_ativa: opcional,
  parte_passiva: opcional,
  classe: opcional,
  assunto: opcional,
  foro_vara: opcional,
  valor_causa: z.string().trim().max(100, 'Valor muito longo'),
  juiz: opcional,
})

export function validarNovaElaboracao(
  rascunho: RascunhoManual,
): { ok: true } | { ok: false; erros: Partial<Record<keyof RascunhoManual, string>> } {
  const resultado = novaElaboracaoSchema.safeParse(rascunho)
  if (resultado.success) {
    return { ok: true }
  }
  const erros: Partial<Record<keyof RascunhoManual, string>> = {}
  for (const issue of resultado.error.issues) {
    const campo = issue.path[0]
    if (typeof campo === 'string' && !(campo in erros)) {
      erros[campo as keyof RascunhoManual] = issue.message
    }
  }
  return { ok: false, erros }
}

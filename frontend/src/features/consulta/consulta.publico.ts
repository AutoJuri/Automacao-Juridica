import { api } from '#/lib/axios'

/** Mesma máscara do backend (`app/core/cnj.py`): com ou sem pontuação, 20 dígitos. */
const CNJ_COMPLETO = /^(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})$/

export type SituacaoConsultaPublica =
  | 'encontrado'
  | 'ausente'
  | 'indisponivel'
  | 'tribunal_nao_suportado'

export interface ConsultaPublica {
  numero: string
  tribunal: string | null
  situacao: SituacaoConsultaPublica
  classe_nome: string | null
  assuntos: { codigo: number | null; nome: string | null }[]
  orgao_julgador: string | null
  data_ajuizamento: string | null
  grau: string | null
  formato: string | null
  sistema: string | null
  atualizado_em: string | null
  sigilo: string | null
  movimentos_total: number
  movimentos: {
    codigo: number | null
    nome: string | null
    data_hora: string | null
    orgao_julgador: string | null
    complementos: string[]
  }[]
}

export function numeroCnjCompleto(valor: string): boolean {
  return CNJ_COMPLETO.test(valor.trim())
}

export function mesmosDigitos(cadastrado: string | null | undefined, busca: string): boolean {
  const daCarteira = (cadastrado ?? '').replace(/\D/g, '')
  const digitado = busca.replace(/\D/g, '')
  return daCarteira.length === 20 && daCarteira === digitado
}

export async function consultarProcessoPublico(numero: string): Promise<ConsultaPublica> {
  const { data } = await api.get<ConsultaPublica>('/processos/publico', {
    params: { numero: numero.trim() },
  })
  return data
}

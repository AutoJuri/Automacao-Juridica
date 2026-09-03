import { textoCampoCpo } from '#/features/processos/processos.dates'
import {
  formatarNumeroCnj,
  juntarLocalProcesso,
  rotuloTribunal,
} from '#/features/processos/processos.format'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'

export const CAMPO_VAZIO = 'Não disponível'

export interface ItemCompletudeProcesso {
  id: string
  label: string
  preenchido: boolean
}

export interface CompletudeProcesso {
  itens: ItemCompletudeProcesso[]
  atendidos: number
  total: number
  percentual: number
}

export interface DadosElaboracao {
  cnj: string
  autor: string
  reu: string
  foroTribunal: string
  valorCausa: string
  juiz: string
  assunto: string
  classe: string
  local: string
}

function textoOuVazio(valor: string | null | undefined, pendente: boolean): string {
  return textoCampoCpo(valor, pendente)
}

export function extrairDadosElaboracao(processo: ProcessoDetalhe): DadosElaboracao {
  const pendente = processo.movimentacoes_status === 'pendente'
  const local = juntarLocalProcesso(
    processo.foro?.trim() ?? '',
    processo.area?.trim() ?? '',
    processo.vara?.trim() ?? '',
  )
  const tribunal = rotuloTribunal(processo.tribunal)
  const foroTribunal = [local || null, tribunal].filter(Boolean).join(' · ')

  return {
    cnj: formatarNumeroCnj(processo.nu_processo),
    autor: processo.parte_ativa?.nome?.trim() || CAMPO_VAZIO,
    reu: processo.parte_passiva?.nome?.trim() || CAMPO_VAZIO,
    foroTribunal: foroTribunal || CAMPO_VAZIO,
    valorCausa: textoOuVazio(processo.valor_acao, pendente),
    juiz: textoOuVazio(processo.juiz, pendente),
    assunto: processo.de_assunto?.trim() || CAMPO_VAZIO,
    classe: processo.de_classe?.trim() || CAMPO_VAZIO,
    local: local || CAMPO_VAZIO,
  }
}

export function completudeDadosProcesso(processo: ProcessoDetalhe): CompletudeProcesso {
  const itens: ItemCompletudeProcesso[] = [
    { id: 'cnj', label: 'Número do processo', preenchido: Boolean(processo.nu_processo?.trim()) },
    { id: 'autor', label: 'Polo ativo', preenchido: Boolean(processo.parte_ativa?.nome?.trim()) },
    { id: 'reu', label: 'Polo passivo', preenchido: Boolean(processo.parte_passiva?.nome?.trim()) },
    {
      id: 'foro',
      label: 'Foro / vara',
      preenchido: Boolean(processo.foro?.trim() || processo.vara?.trim()),
    },
    { id: 'valor', label: 'Valor da causa', preenchido: Boolean(processo.valor_acao?.trim()) },
    { id: 'juiz', label: 'Magistrado', preenchido: Boolean(processo.juiz?.trim()) },
    { id: 'assunto', label: 'Assunto', preenchido: Boolean(processo.de_assunto?.trim()) },
  ]
  const atendidos = itens.filter((item) => item.preenchido).length
  return {
    itens,
    atendidos,
    total: itens.length,
    percentual: itens.length === 0 ? 0 : Math.round((atendidos / itens.length) * 100),
  }
}

export function montarEnderecamento(processo: ProcessoDetalhe): string {
  const vara = processo.vara?.trim()
  const foro = processo.foro?.trim()
  if (vara && foro) {
    return `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ${vara.toUpperCase()} DO ${foro.toUpperCase()}`
  }
  if (vara) {
    return `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ${vara.toUpperCase()}`
  }
  if (foro) {
    return `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DO ${foro.toUpperCase()}`
  }
  return 'EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO'
}

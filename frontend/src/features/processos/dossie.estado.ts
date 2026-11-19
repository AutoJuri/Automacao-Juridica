const ROTULO_DOCUMENTO: Record<string, string> = {
  pendente: 'Pendente',
  lido: 'Lido',
  parcial: 'Parcial',
  sem_acesso: 'Sem acesso',
  ilegivel: 'Ilegível',
  erro: 'Erro',
}

export function textoProgresso(lidos: number, total: number): string {
  return `${lidos} de ${total} documentos`
}

export function percentualLeitura(lidos: number, total: number): number {
  if (total <= 0) {
    return 0
  }
  return Math.min(100, Math.round((lidos / total) * 100))
}

export function rotuloFaixaAutos(
  status: string | undefined,
  lidos: number,
  total: number,
): string {
  if (status === 'lendo') {
    return 'Lendo autos'
  }
  if (total > 0 && lidos >= total) {
    return 'Autos lidos'
  }
  if (total > 0 && lidos > 0) {
    return textoProgresso(lidos, total)
  }
  if (status === 'erro') {
    return 'Leitura com erro'
  }
  if (status === 'sessao_expirada') {
    return 'Sessão do e-SAJ expirada'
  }
  return 'Autos não lidos'
}

export type EtapaPreparacao = 1 | 2 | 3 | 5

export function etapaPreparacao(
  status: string | undefined,
  lidos: number,
  total: number,
  temResumo: boolean,
  temTeseOuPedido: boolean,
): EtapaPreparacao {
  const leituraIncompleta =
    !status ||
    status === 'ocioso' ||
    status === 'lendo' ||
    (lidos === 0 && total === 0 && status !== 'pronto') ||
    (total > 0 && lidos < total)
  if (leituraIncompleta && !temResumo) {
    return 1
  }
  if (!temResumo) {
    return 2
  }
  if (!temTeseOuPedido) {
    return 3
  }
  return 5
}

export interface RoteiroPeca {
  resumo: string
  tese: string
  pedidos: string
  acrescentar: string
  nao_incluir: string
  jurisprudencia: string
}

export const ROTEIRO_VAZIO: RoteiroPeca = {
  resumo: '',
  tese: '',
  pedidos: '',
  acrescentar: '',
  nao_incluir: '',
  jurisprudencia: '',
}

const LIMITE_FATOS = 8000

export function textoDoRoteiro(roteiro: RoteiroPeca): string {
  const blocos: Array<[string, string]> = [
    ['Resumo ajustado', roteiro.resumo],
    ['Tese', roteiro.tese],
    ['Pedidos', roteiro.pedidos],
    ['Pontos a acrescentar', roteiro.acrescentar],
    ['Não incluir', roteiro.nao_incluir],
    ['Jurisprudência colada pelo advogado', roteiro.jurisprudencia],
  ]
  const texto = blocos
    .filter(([, valor]) => valor.trim())
    .map(([titulo, valor]) => `${titulo}:\n${valor.trim()}`)
    .join('\n\n')
  return texto.slice(0, LIMITE_FATOS)
}

export function deveAcompanhar(status: string | undefined): boolean {
  return status === 'lendo'
}

export function rotuloDocumento(status: string): string {
  return ROTULO_DOCUMENTO[status] ?? 'Pendente'
}

export function rotuloBotao(status: string, lidos: number, total: number): string {
  if (status === 'lendo') {
    return 'Lendo autos…'
  }
  if (lidos > 0 && lidos < total) {
    return 'Continuar leitura'
  }
  if (status === 'pronto' || status === 'sem_documentos') {
    return 'Ler de novo'
  }
  return 'Ler autos'
}

export function notaElaborar(status: string, quando: string | null): string {
  if (status === 'lendo') {
    return 'Leitura dos autos em andamento. O Elaborar usa o resumo quando ela terminar.'
  }
  if (quando && (status === 'pronto' || status === 'bloqueado' || status === 'limite_ia')) {
    return `Autos lidos em ${quando}. O Elaborar usa esse resumo.`
  }
  return 'Autos ainda não lidos. O Elaborar não verá a pasta.'
}

export function avisoStatus(status: string): string | null {
  if (status === 'sessao_expirada') {
    return 'A pasta dos autos pediu um novo login. Reconecte o e-SAJ em Configurações e tente de novo.'
  }
  if (status === 'bloqueado') {
    return 'O e-SAJ limitou a leitura. O cookie continua válido. Tente de novo mais tarde.'
  }
  if (status === 'limite_ia') {
    return 'A leitura pausou porque o provedor de IA limitou as chamadas. Continue mais tarde.'
  }
  if (status === 'erro') {
    return 'A leitura parou com erro. Os documentos já lidos foram mantidos.'
  }
  if (status === 'sem_documentos') {
    return 'Este processo não tem o link da pasta digital.'
  }
  return null
}

export function temSemAcesso(statuses: string[]): boolean {
  return statuses.includes('sem_acesso')
}

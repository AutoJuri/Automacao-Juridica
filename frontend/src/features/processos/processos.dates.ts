const TZ_SP = 'America/Sao_Paulo'

export function formatarDataSP(iso: string | null | undefined): string {
  if (!iso) {
    return 'Não disponível'
  }
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) {
    return 'Não disponível'
  }
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ_SP,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(data)
}

export function formatarDataHoraSP(iso: string | null | undefined): string {
  if (!iso) {
    return 'Não disponível'
  }
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) {
    return 'Não disponível'
  }
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ_SP,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(data)
}

export function textoCampoCpo(
  valor: string | null | undefined,
  aindaNaoBuscado: boolean,
): string {
  const texto = valor?.trim()
  if (texto) {
    return texto
  }
  if (aindaNaoBuscado) {
    return 'Ainda não buscado no CPO'
  }
  return 'Não disponível'
}

export type PrazoUrgencia = 'verde' | 'amarelo' | 'vermelho'

const CORES: Record<PrazoUrgencia, string> = {
  verde: '#22C55E',
  amarelo: '#F59E0B',
  vermelho: '#EF4444',
}

/** Converte data no formato DD/MM/YYYY para Date local. */
export function parseDataBR(data: string): Date {
  const [dia, mes, ano] = data.split('/').map(Number)
  return new Date(ano, mes - 1, dia)
}

/**
 * Calcula a cor do prazo com base na proporção de tempo restante.
 * Verde: > 2/3 do prazo restante | Amarelo: > 1/3 | Vermelho: ≤ 1/3
 */
export function getPrazoUrgencia(
  prazoInicio: string,
  prazoFim: string,
  referencia: Date = new Date(),
): { cor: string; urgencia: PrazoUrgencia } {
  const inicio = parseDataBR(prazoInicio)
  const fim = parseDataBR(prazoFim)

  const totalMs = fim.getTime() - inicio.getTime()
  if (totalMs <= 0) {
    return { cor: CORES.vermelho, urgencia: 'vermelho' }
  }

  const restanteMs = fim.getTime() - referencia.getTime()
  if (restanteMs <= 0) {
    return { cor: CORES.vermelho, urgencia: 'vermelho' }
  }

  const proporcaoRestante = restanteMs / totalMs

  if (proporcaoRestante > 2 / 3) {
    return { cor: CORES.verde, urgencia: 'verde' }
  }
  if (proporcaoRestante > 1 / 3) {
    return { cor: CORES.amarelo, urgencia: 'amarelo' }
  }
  return { cor: CORES.vermelho, urgencia: 'vermelho' }
}

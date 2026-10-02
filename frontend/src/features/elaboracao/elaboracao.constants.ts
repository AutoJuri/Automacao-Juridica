export function elaboracaoSessaoQueryKey(processoId: string, peca: string) {
  return ['elaboracao', processoId, peca] as const
}

export function elaboracaoVersoesQueryKey(elaboracaoId: string | null) {
  return ['elaboracao-versoes', elaboracaoId] as const
}

export function sugestaoPecaQueryKey(processoId: string | null) {
  return ['elaboracao-sugestao-peca', processoId] as const
}

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '#/lib/axios'

/**
 * PDF da movimentação, pelo nosso servidor (ADR-027). O cookie do e-SAJ fica no
 * backend; aqui chega só o arquivo, em memória. Nada vai para storage.
 */
export async function buscarPdfDaMovimentacao(
  processoId: string,
  movimentacaoId: string,
): Promise<Blob> {
  const { data } = await api.get<Blob>(
    `/processos/${processoId}/movimentacoes/${movimentacaoId}/documento`,
    { responseType: 'blob' },
  )
  return new Blob([data], { type: 'application/pdf' })
}

export interface PdfDaMovimentacao {
  /** `blob:` da própria aba. Some ao fechar o visualizador. */
  url: string | null
  carregando: boolean
  erro: unknown
}

export function usePdfDaMovimentacao(
  processoId: string | null,
  movimentacaoId: string,
  ativo: boolean,
): PdfDaMovimentacao {
  const habilitado = ativo && processoId !== null
  const consulta = useQuery({
    queryKey: ['processos', processoId, 'movimentacoes', movimentacaoId, 'pdf'],
    queryFn: () => buscarPdfDaMovimentacao(processoId as string, movimentacaoId),
    enabled: habilitado,
    // O arquivo é sigiloso: não fica em cache depois que a tela fecha.
    gcTime: 0,
    staleTime: 0,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const [url, setUrl] = useState<string | null>(null)
  const blob = consulta.data

  useEffect(() => {
    if (!blob) {
      setUrl(null)
      return
    }
    const criada = URL.createObjectURL(blob)
    setUrl(criada)
    return () => URL.revokeObjectURL(criada)
  }, [blob])

  return {
    url,
    carregando: habilitado && (consulta.isPending || (blob !== undefined && url === null)),
    erro: consulta.error,
  }
}

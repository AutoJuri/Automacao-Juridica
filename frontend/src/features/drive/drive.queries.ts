import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  atualizarPasta,
  baixarArquivo,
  buscarPasta,
  buscarStatusGoogle,
  buscarUrlDeAutorizacaoDrive,
  criarPasta,
  desconectarGoogle,
  enviarArquivo,
  excluirArquivo,
  excluirPasta,
  listarArquivos,
  listarPastas,
  moverArquivo,
  vincularArquivoDoGoogle,
} from './drive.api'
import {
  DRIVE_QUERY_KEY,
  driveArquivosKey,
  driveGoogleStatusKey,
  drivePastaKey,
  drivePastasKey,
} from './drive.constants'
import type { AtualizarPasta } from './drive.types'

export function usePastas() {
  return useQuery({ queryKey: drivePastasKey(), queryFn: listarPastas })
}

export function usePasta(id: string) {
  return useQuery({
    queryKey: drivePastaKey(id),
    queryFn: () => buscarPasta(id),
  })
}

export function useCriarPasta() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (entrada: { nome: string; processoId: string | null }) =>
      criarPasta(entrada.nome, entrada.processoId),
    onSuccess: async () => {
      await cliente.invalidateQueries({ queryKey: DRIVE_QUERY_KEY })
    },
  })
}

export function useAtualizarPasta() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (entrada: { id: string; corpo: AtualizarPasta }) =>
      atualizarPasta(entrada.id, entrada.corpo),
    onSuccess: async () => {
      await cliente.invalidateQueries({ queryKey: DRIVE_QUERY_KEY })
    },
  })
}

export function useExcluirPasta() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: excluirPasta,
    onSuccess: async () => {
      await cliente.invalidateQueries({ queryKey: DRIVE_QUERY_KEY })
    },
  })
}

// --- Conexão com o Google ---------------------------------------------------

export function useStatusGoogle() {
  return useQuery({
    queryKey: driveGoogleStatusKey(),
    queryFn: buscarStatusGoogle,
  })
}

export function useConectarGoogle() {
  return useMutation({
    mutationFn: buscarUrlDeAutorizacaoDrive,
    onSuccess: ({ authorize_url }) => {
      // Navegação de página inteira: o consentimento acontece no domínio do Google.
      window.location.href = authorize_url
    },
  })
}

export function useDesconectarGoogle() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: desconectarGoogle,
    onSuccess: async (status) => {
      cliente.setQueryData(driveGoogleStatusKey(), status)
      await cliente.invalidateQueries({ queryKey: DRIVE_QUERY_KEY })
    },
  })
}

// --- Arquivos ---------------------------------------------------------------

export function useArquivos(pastaId: string) {
  return useQuery({
    queryKey: driveArquivosKey(pastaId),
    queryFn: () => listarArquivos(pastaId),
  })
}

/** Qualquer mudança em arquivos mexe também na contagem das pastas. */
function useInvalidarDrive() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: DRIVE_QUERY_KEY })
}

export function useEnviarArquivo() {
  const invalidar = useInvalidarDrive()
  return useMutation({
    mutationFn: (entrada: { pastaId: string; arquivo: File; origem?: 'upload' | 'elaboracao' }) =>
      enviarArquivo(entrada.pastaId, entrada.arquivo, entrada.origem),
    onSuccess: invalidar,
  })
}

export function useVincularArquivo() {
  const invalidar = useInvalidarDrive()
  return useMutation({
    mutationFn: (entrada: { pastaId: string; googleFileId: string }) =>
      vincularArquivoDoGoogle(entrada.pastaId, entrada.googleFileId),
    onSuccess: invalidar,
  })
}

export function useBaixarArquivo() {
  const invalidar = useInvalidarDrive()
  return useMutation({
    mutationFn: baixarArquivo,
    // O backend marca "ausente no Google" quando o arquivo some: recarrega a lista.
    onError: invalidar,
  })
}

export function useMoverArquivo() {
  const invalidar = useInvalidarDrive()
  return useMutation({
    mutationFn: (entrada: { id: string; pastaId: string }) =>
      moverArquivo(entrada.id, entrada.pastaId),
    onSuccess: invalidar,
  })
}

export function useExcluirArquivo() {
  const invalidar = useInvalidarDrive()
  return useMutation({
    mutationFn: excluirArquivo,
    onSuccess: invalidar,
  })
}

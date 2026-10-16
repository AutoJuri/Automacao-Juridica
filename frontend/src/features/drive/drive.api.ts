import { api } from '#/lib/axios'

import type { ArquivoDrive, AtualizarPasta, DriveStatus, Pasta, PickerToken } from './drive.types'

export async function listarPastas(): Promise<Pasta[]> {
  const { data } = await api.get<Pasta[]>('/drive/pastas')
  return data
}

export async function buscarPasta(id: string): Promise<Pasta> {
  const { data } = await api.get<Pasta>(`/drive/pastas/${id}`)
  return data
}

export async function criarPasta(nome: string, processoId: string | null): Promise<Pasta> {
  const { data } = await api.post<Pasta>('/drive/pastas', {
    nome: nome.trim(),
    ...(processoId ? { processo_id: processoId } : {}),
  })
  return data
}

export async function atualizarPasta(id: string, corpo: AtualizarPasta): Promise<Pasta> {
  const { data } = await api.patch<Pasta>(`/drive/pastas/${id}`, corpo)
  return data
}

export async function excluirPasta(id: string): Promise<void> {
  await api.delete(`/drive/pastas/${id}`)
}

// --- Conexão com o Google ---------------------------------------------------

export async function buscarStatusGoogle(): Promise<DriveStatus> {
  const { data } = await api.get<DriveStatus>('/drive/google/status')
  return data
}

export async function buscarUrlDeAutorizacaoDrive(): Promise<{
  authorize_url: string
}> {
  const { data } = await api.get<{ authorize_url: string }>('/drive/google/authorize')
  return data
}

export async function desconectarGoogle(): Promise<DriveStatus> {
  const { data } = await api.delete<DriveStatus>('/drive/google')
  return data
}

/** Token curto só para o seletor do Google. Nunca é guardado em storage. */
export async function buscarTokenDoPicker(): Promise<PickerToken> {
  const { data } = await api.post<PickerToken>('/drive/google/picker-token')
  return data
}

// --- Arquivos ---------------------------------------------------------------

export async function listarArquivos(pastaId: string): Promise<ArquivoDrive[]> {
  const { data } = await api.get<ArquivoDrive[]>(`/drive/pastas/${pastaId}/arquivos`)
  return data
}

export async function enviarArquivo(
  pastaId: string,
  arquivo: File,
  origem: 'upload' | 'elaboracao' = 'upload',
): Promise<ArquivoDrive> {
  const corpo = new FormData()
  corpo.append('arquivo', arquivo)
  corpo.append('origem', origem)
  // O browser monta o boundary do multipart; o axios só não pode forçar JSON.
  const { data } = await api.post<ArquivoDrive>(`/drive/pastas/${pastaId}/arquivos`, corpo, {
    headers: { 'Content-Type': undefined },
    timeout: 120_000,
  })
  return data
}

export async function vincularArquivoDoGoogle(
  pastaId: string,
  googleFileId: string,
): Promise<ArquivoDrive> {
  const { data } = await api.post<ArquivoDrive>(`/drive/pastas/${pastaId}/arquivos/vincular`, {
    google_file_id: googleFileId,
  })
  return data
}

export async function baixarArquivo(id: string): Promise<Blob> {
  const { data } = await api.get<Blob>(`/drive/arquivos/${id}/conteudo`, {
    responseType: 'blob',
    timeout: 120_000,
  })
  return data
}

export async function moverArquivo(id: string, pastaId: string): Promise<ArquivoDrive> {
  const { data } = await api.patch<ArquivoDrive>(`/drive/arquivos/${id}`, {
    pasta_id: pastaId,
  })
  return data
}

export async function excluirArquivo(id: string): Promise<void> {
  await api.delete(`/drive/arquivos/${id}`)
}

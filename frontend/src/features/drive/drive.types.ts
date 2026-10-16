export interface PastaProcesso {
  id: string
  nu_processo: string | null
  autor: string | null
  reu: string | null
}

export interface Pasta {
  id: string
  nome: string
  processo: PastaProcesso | null
  total_arquivos: number
  updated_at: string
}

export interface AtualizarPasta {
  nome?: string
  /** `null` solta o vínculo; ausente mantém. */
  processo_id?: string | null
}

export interface DriveStatus {
  /** O servidor tem as chaves do Google para conectar. */
  configurado: boolean
  /** O servidor tem as chaves para abrir o seletor do Google. */
  picker_configurado: boolean
  conectado: boolean
}

export interface PickerToken {
  access_token: string
  expires_in: number
  api_key: string
  app_id: string
}

export type OrigemArquivo = 'upload' | 'drive' | 'elaboracao'

export interface ArquivoDrive {
  id: string
  pasta_id: string
  nome: string
  mime_type: string
  tamanho: number | null
  origem: OrigemArquivo
  ausente_no_google: boolean
  url_drive: string
  created_at: string
}

export const DRIVE_QUERY_KEY = ['drive'] as const

export const drivePastasKey = () => [...DRIVE_QUERY_KEY, 'pastas'] as const
export const drivePastaKey = (id: string) => [...DRIVE_QUERY_KEY, 'pasta', id] as const
export const driveGoogleStatusKey = () => [...DRIVE_QUERY_KEY, 'google-status'] as const
export const driveArquivosKey = (pastaId: string) =>
  [...DRIVE_QUERY_KEY, 'arquivos', pastaId] as const

export const NOME_PASTA_MAX = 120

/** Mesmo teto do backend (`TAMANHO_MAX`). O servidor revalida: isto é só UX. */
export const TAMANHO_MAX_ARQUIVO = 25 * 1024 * 1024

/** Tipos aceitos na área de arquivos. Executáveis ficam de fora. */
export const TIPOS_DE_ARQUIVO = [
  { rotulo: 'PDF', extensoes: ['.pdf'] },
  { rotulo: 'Word', extensoes: ['.doc', '.docx'] },
  { rotulo: 'Texto', extensoes: ['.txt', '.rtf', '.odt'] },
  { rotulo: 'Imagem', extensoes: ['.png', '.jpg', '.jpeg'] },
] as const

export const EXTENSOES_ACEITAS: readonly string[] = TIPOS_DE_ARQUIVO.flatMap(
  (tipo) => tipo.extensoes,
)

/** Tipos que o seletor do Google mostra. O backend revalida ao vincular. */
export const MIMES_DO_SELETOR = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.oasis.opendocument.text',
  'text/plain',
  'application/rtf',
  'image/png',
  'image/jpeg',
] as const

/** Resultado que o callback do Google deixa em `/drive?google=...`. */
export const PARAM_RESULTADO_GOOGLE = 'google'

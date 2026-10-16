import { EXTENSOES_ACEITAS, TAMANHO_MAX_ARQUIVO } from './drive.constants'

export function rotuloArquivos(total: number): string {
  if (total === 0) {
    return 'Nenhum arquivo'
  }
  return total === 1 ? '1 arquivo' : `${total} arquivos`
}

/** `null` quando o Google não informa o tamanho (ex.: arquivo escolhido no seletor). */
export function rotuloTamanho(bytes: number | null): string {
  if (bytes === null) {
    return '—'
  }
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0).replace('.', ',')} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} MB`
}

export function dataDoArquivo(iso: string): string {
  const data = new Date(iso)
  return Number.isNaN(data.getTime()) ? '' : data.toLocaleDateString('pt-BR')
}

export function extensaoDoNome(nome: string): string {
  const ponto = nome.lastIndexOf('.')
  return ponto <= 0 ? '' : nome.slice(ponto).toLowerCase()
}

/** Pré-checagem de UX antes do envio. O backend repete todas as regras. */
export function problemaDoArquivo(arquivo: { name: string; size: number }): string | null {
  if (arquivo.size === 0) {
    return `“${arquivo.name}” está vazio.`
  }
  if (arquivo.size > TAMANHO_MAX_ARQUIVO) {
    return `“${arquivo.name}” passa de 25 MB.`
  }
  if (!EXTENSOES_ACEITAS.includes(extensaoDoNome(arquivo.name))) {
    return `“${arquivo.name}” não é de um tipo aceito (${EXTENSOES_ACEITAS.join(', ')}).`
  }
  return null
}

const ROTULO_ORIGEM: Record<string, string> = {
  upload: 'Enviado',
  drive: 'Do Google Drive',
  elaboracao: 'Da elaboração',
}

export function rotuloOrigem(origem: string): string {
  return ROTULO_ORIGEM[origem] ?? origem
}

/** Apelido curto do tipo para o ícone/etiqueta da lista. */
export function rotuloTipo(mime: string, nome: string): string {
  if (mime === 'application/pdf') {
    return 'PDF'
  }
  if (mime.startsWith('image/')) {
    return 'Imagem'
  }
  const extensao = extensaoDoNome(nome)
  if (['.doc', '.docx', '.odt', '.rtf'].includes(extensao)) {
    return 'Documento'
  }
  return extensao ? extensao.slice(1).toUpperCase() : 'Arquivo'
}

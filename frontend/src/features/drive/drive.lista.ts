import { extensaoDoNome } from './drive.format';

/** Grupo usado no filtro. "outro" não tem botão: só aparece em "Todos". */
export type GrupoArquivo = 'pdf' | 'word' | 'texto' | 'imagem' | 'outro';

export type FiltroTipoArquivo = 'todos' | Exclude<GrupoArquivo, 'outro'>;

export type OrdemArquivo = 'nome-asc' | 'nome-desc' | 'data-desc' | 'data-asc';

export type VistaArquivo = 'lista' | 'grade';

const EXTENSAO_WORD = ['.doc', '.docx'];
const EXTENSAO_TEXTO = ['.txt', '.rtf', '.odt'];
const EXTENSAO_IMAGEM = ['.png', '.jpg', '.jpeg'];
const MIME_WORD = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

interface ArquivoOrdenavel {
  nome: string;
  mime_type: string;
  created_at: string;
}

export function grupoArquivo(arquivo: { nome: string; mime_type: string }): GrupoArquivo {
  const extensao = extensaoDoNome(arquivo.nome);
  const mime = arquivo.mime_type;
  if (mime === 'application/pdf' || extensao === '.pdf') {
    return 'pdf';
  }
  if (mime.startsWith('image/') || EXTENSAO_IMAGEM.includes(extensao)) {
    return 'imagem';
  }
  if (EXTENSAO_WORD.includes(extensao) || mime === 'application/msword' || mime === MIME_WORD) {
    return 'word';
  }
  if (
    EXTENSAO_TEXTO.includes(extensao) ||
    mime === 'text/plain' ||
    mime === 'application/rtf' ||
    mime === 'application/vnd.oasis.opendocument.text'
  ) {
    return 'texto';
  }
  return 'outro';
}

function instante(iso: string): number {
  const valor = new Date(iso).getTime();
  return Number.isNaN(valor) ? 0 : valor;
}

/** Filtra pelo tipo e ordena. A data é a de entrada na pasta (`created_at`). */
export function organizarArquivos<T extends ArquivoOrdenavel>(
  itens: readonly T[],
  filtro: FiltroTipoArquivo,
  ordem: OrdemArquivo,
): T[] {
  const base =
    filtro === 'todos' ? [...itens] : itens.filter((item) => grupoArquivo(item) === filtro);
  base.sort((a, b) => {
    if (ordem === 'nome-asc' || ordem === 'nome-desc') {
      const porNome = a.nome.localeCompare(b.nome, 'pt-BR', { sensitivity: 'base', numeric: true });
      if (porNome !== 0) {
        return ordem === 'nome-asc' ? porNome : -porNome;
      }
    }
    const porData = instante(a.created_at) - instante(b.created_at);
    return ordem === 'data-asc' || ordem === 'nome-asc' ? porData : -porData;
  });
  return base;
}

function semAcento(valor: string): string {
  return valor.normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('pt-BR');
}

/** Busca pelo nome, ignorando maiúsculas e acento. Termo vazio aceita tudo. */
export function nomeCombina(nome: string, termo: string): boolean {
  const busca = semAcento(termo.trim());
  if (!busca) {
    return true;
  }
  return semAcento(nome).includes(busca);
}

const CHAVE_VISTA = 'drive.vista';

export function lerVistaArquivos(): VistaArquivo {
  try {
    return localStorage.getItem(CHAVE_VISTA) === 'grade' ? 'grade' : 'lista';
  } catch {
    return 'lista';
  }
}

export function guardarVistaArquivos(vista: VistaArquivo): void {
  try {
    localStorage.setItem(CHAVE_VISTA, vista);
  } catch {
    // Preferência visual. A tela continua mesmo se o navegador bloquear o storage.
  }
}

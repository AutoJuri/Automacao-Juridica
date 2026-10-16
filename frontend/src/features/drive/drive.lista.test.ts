import { describe, expect, it } from 'vitest';

import { grupoArquivo, nomeCombina, organizarArquivos } from './drive.lista';

function arquivo(nome: string, mime: string, created_at: string) {
  return { nome, mime_type: mime, created_at };
}

const ITENS = [
  arquivo('beta.pdf', 'application/pdf', '2026-10-02T12:00:00Z'),
  arquivo('alfa.txt', 'text/plain', '2026-10-14T12:00:00Z'),
  arquivo('foto.png', 'image/png', '2026-10-01T12:00:00Z'),
  arquivo(
    'peca.docx',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '2026-10-10T12:00:00Z',
  ),
];

describe('grupoArquivo', () => {
  it('separa PDF, Word, texto e imagem', () => {
    expect(grupoArquivo(ITENS[0])).toBe('pdf');
    expect(grupoArquivo(ITENS[1])).toBe('texto');
    expect(grupoArquivo(ITENS[2])).toBe('imagem');
    expect(grupoArquivo(ITENS[3])).toBe('word');
  });
});

describe('organizarArquivos', () => {
  it('ordena o nome de A a Z e de Z a A', () => {
    expect(organizarArquivos(ITENS, 'todos', 'nome-asc').map((item) => item.nome)).toEqual([
      'alfa.txt',
      'beta.pdf',
      'foto.png',
      'peca.docx',
    ]);
    expect(organizarArquivos(ITENS, 'todos', 'nome-desc').map((item) => item.nome)).toEqual([
      'peca.docx',
      'foto.png',
      'beta.pdf',
      'alfa.txt',
    ]);
  });

  it('ordena pela data de entrada, mais recente primeiro', () => {
    expect(organizarArquivos(ITENS, 'todos', 'data-desc').map((item) => item.nome)).toEqual([
      'alfa.txt',
      'peca.docx',
      'beta.pdf',
      'foto.png',
    ]);
    expect(organizarArquivos(ITENS, 'todos', 'data-asc').map((item) => item.nome)[0]).toBe(
      'foto.png',
    );
  });

  it('acha o nome sem diferenciar maiúscula nem acento', () => {
    expect(nomeCombina('Petição inicial.pdf', '')).toBe(true);
    expect(nomeCombina('Petição inicial.pdf', '  peticao ')).toBe(true);
    expect(nomeCombina('Petição inicial.pdf', 'contrato')).toBe(false);
  });

  it('filtra pelo tipo e mantém a ordem', () => {
    expect(organizarArquivos(ITENS, 'pdf', 'nome-asc').map((item) => item.nome)).toEqual([
      'beta.pdf',
    ]);
    expect(organizarArquivos(ITENS, 'imagem', 'data-desc')).toHaveLength(1);
  });
});

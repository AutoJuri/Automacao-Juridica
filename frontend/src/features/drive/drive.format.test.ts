import { describe, expect, it } from 'vitest'

import { TAMANHO_MAX_ARQUIVO, TIPOS_DE_ARQUIVO } from './drive.constants'
import {
  extensaoDoNome,
  problemaDoArquivo,
  rotuloArquivos,
  rotuloOrigem,
  rotuloTamanho,
  rotuloTipo,
} from './drive.format'

describe('rotuloArquivos', () => {
  it('descreve zero, um e vários arquivos', () => {
    expect(rotuloArquivos(0)).toBe('Nenhum arquivo')
    expect(rotuloArquivos(1)).toBe('1 arquivo')
    expect(rotuloArquivos(7)).toBe('7 arquivos')
  })
})

describe('TIPOS_DE_ARQUIVO', () => {
  it('prevê PDF e Word e deixa executáveis de fora', () => {
    const extensoes: string[] = TIPOS_DE_ARQUIVO.flatMap((tipo) => [...tipo.extensoes])
    expect(extensoes).toEqual(expect.arrayContaining(['.pdf', '.doc', '.docx']))
    expect(extensoes).not.toContain('.exe')
    expect(extensoes).not.toContain('.js')
  })
})

describe('rotuloTamanho', () => {
  it('usa B, KB e MB e aceita tamanho desconhecido', () => {
    expect(rotuloTamanho(null)).toBe('—')
    expect(rotuloTamanho(512)).toBe('512 B')
    expect(rotuloTamanho(2048)).toBe('2,0 KB')
    expect(rotuloTamanho(300 * 1024)).toBe('300 KB')
    expect(rotuloTamanho(5 * 1024 * 1024)).toBe('5,0 MB')
  })
})

describe('extensaoDoNome', () => {
  it('devolve a extensão em minúsculas e ignora nomes sem ponto', () => {
    expect(extensaoDoNome('Peticao.PDF')).toBe('.pdf')
    expect(extensaoDoNome('arquivo')).toBe('')
    expect(extensaoDoNome('.env')).toBe('')
  })
})

describe('problemaDoArquivo', () => {
  it('aceita arquivo dentro das regras', () => {
    expect(problemaDoArquivo({ name: 'a.pdf', size: 10 })).toBeNull()
  })

  it('recusa vazio, grande demais e tipo fora da lista', () => {
    expect(problemaDoArquivo({ name: 'a.pdf', size: 0 })).toContain('vazio')
    expect(problemaDoArquivo({ name: 'a.pdf', size: TAMANHO_MAX_ARQUIVO + 1 })).toContain('25 MB')
    expect(problemaDoArquivo({ name: 'virus.exe', size: 10 })).toContain('tipo aceito')
  })
})

describe('rótulos de origem e tipo', () => {
  it('traduz a origem e resume o tipo', () => {
    expect(rotuloOrigem('drive')).toBe('Do Google Drive')
    expect(rotuloOrigem('elaboracao')).toBe('Da elaboração')
    expect(rotuloTipo('application/pdf', 'x.pdf')).toBe('PDF')
    expect(rotuloTipo('image/png', 'x.png')).toBe('Imagem')
    expect(rotuloTipo('application/msword', 'x.docx')).toBe('Documento')
  })
})

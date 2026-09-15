import { describe, expect, it } from 'vitest'

import {
  hrefDocumentoMovimentacao,
  urlDocumentoEsaj,
  urlEsajHttps,
} from './processos.urls'

const DOCUMENTO =
  'https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?cdDocumento=1'
const CPO = 'https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo=ABC'

describe('urlEsajHttps', () => {
  it('aceita https do host do e-SAJ', () => {
    expect(urlEsajHttps(CPO)).toBe(CPO)
  })

  it('rejeita javascript e outro host', () => {
    expect(urlEsajHttps('javascript:alert(1)')).toBeNull()
    expect(urlEsajHttps('https://evil.example/x')).toBeNull()
    expect(urlEsajHttps('http://esaj.tjsp.jus.br/cpopg/show.do')).toBeNull()
  })
})

describe('urlDocumentoEsaj', () => {
  it('aceita so o path de documento vinculado', () => {
    expect(urlDocumentoEsaj(DOCUMENTO)).toBe(DOCUMENTO)
    expect(urlDocumentoEsaj(CPO)).toBeNull()
  })
})

describe('hrefDocumentoMovimentacao', () => {
  it('nao gera href sem documento', () => {
    expect(hrefDocumentoMovimentacao(false, DOCUMENTO, CPO)).toBeNull()
  })

  it('prefere a url direta do documento', () => {
    expect(hrefDocumentoMovimentacao(true, DOCUMENTO, CPO)).toBe(DOCUMENTO)
  })

  it('cai na ficha CPO quando o portal so tem hash de senha dos autos', () => {
    expect(hrefDocumentoMovimentacao(true, null, CPO)).toBe(CPO)
  })

  it('nao usa href inseguro mesmo com tem_documento', () => {
    expect(hrefDocumentoMovimentacao(true, 'javascript:alert(1)', null)).toBeNull()
  })
})

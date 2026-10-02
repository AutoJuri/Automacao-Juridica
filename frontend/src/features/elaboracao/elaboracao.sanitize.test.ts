/** @vitest-environment jsdom */
import { describe, expect, it } from 'vitest'

import { sanitizarHtmlMinuta } from './elaboracao.sanitize'

describe('sanitizarHtmlMinuta', () => {
  it('mantem p, strong e em e descarta style e script', () => {
    const html = sanitizarHtmlMinuta(
      '<p style="color:red"><strong>Aviso</strong> <em>teste</em><script>alert(1)</script></p>',
    )

    expect(html).toContain('<strong>Aviso</strong>')
    expect(html).toContain('<em>teste</em>')
    expect(html).not.toContain('style')
    expect(html).not.toContain('script')
    expect(html).not.toContain('alert')
  })
})

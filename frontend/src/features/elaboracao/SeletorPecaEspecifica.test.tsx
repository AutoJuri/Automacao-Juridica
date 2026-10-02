/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SeletorPecaEspecifica } from './SeletorPecaEspecifica'

function componente(overrides: Partial<Parameters<typeof SeletorPecaEspecifica>[0]> = {}) {
  const props = {
    elaboracaoId: 'elaboracao-1',
    estiloAtual: null,
    onSalvarEstilo: vi.fn(),
    salvandoEstilo: false,
    desabilitado: false,
    ...overrides,
  }
  render(<SeletorPecaEspecifica {...props} />)
  return props
}

afterEach(() => {
  cleanup()
})

describe('SeletorPecaEspecifica', () => {
  it('sem texto o botão "Aplicar estilo" fica desabilitado', () => {
    componente()

    const botao = screen.getByRole('button', { name: 'Aplicar estilo' }) as HTMLButtonElement
    expect(botao.disabled).toBe(true)
  })

  it('sem sessão de elaboração (elaboracaoId nulo) fica desabilitado mesmo com texto', () => {
    componente({ elaboracaoId: null })

    fireEvent.change(screen.getByPlaceholderText('Ou cole aqui o texto da tese/modelo...'), {
      target: { value: 'Texto colado do modelo.' },
    })

    const botao = screen.getByRole('button', { name: 'Aplicar estilo' }) as HTMLButtonElement
    expect(botao.disabled).toBe(true)
  })

  it('com texto e sessão pronta, clicar chama onSalvarEstilo com o texto', () => {
    const props = componente()

    fireEvent.change(screen.getByPlaceholderText('Ou cole aqui o texto da tese/modelo...'), {
      target: { value: '  Texto colado do modelo.  ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar estilo' }))

    expect(props.onSalvarEstilo).toHaveBeenCalledWith('Texto colado do modelo.')
  })

  it('estilo já aplicado mostra o aviso correspondente', () => {
    componente({ estiloAtual: '{"modo":"stub"}' })

    expect(
      screen.getByText('Estilo desta sessão já aplicado a partir de um modelo enviado.'),
    ).toBeTruthy()
  })

  it('salvando mostra "Aplicando…" e desabilita o botão', () => {
    componente({ salvandoEstilo: true })

    fireEvent.change(screen.getByPlaceholderText('Ou cole aqui o texto da tese/modelo...'), {
      target: { value: 'Texto qualquer.' },
    })

    const botao = screen.getByRole('button', { name: 'Aplicando…' }) as HTMLButtonElement
    expect(botao.disabled).toBe(true)
  })
})

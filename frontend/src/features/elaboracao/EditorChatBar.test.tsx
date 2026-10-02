/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EditorChatBar } from './EditorChatBar'

function barra(overrides: Partial<Parameters<typeof EditorChatBar>[0]> = {}) {
  const props = {
    chatInput: '',
    onChange: vi.fn(),
    highlightAtivo: false,
    iconesJuris: false,
    onToggleHighlight: vi.fn(),
    onToggleIcones: vi.fn(),
    podeElaborar: true,
    elaborando: false,
    onElaborar: vi.fn(),
    podeConversar: false,
    enviandoChat: false,
    onEnviarChat: vi.fn(),
    erro: null,
    ...overrides,
  }
  render(<EditorChatBar {...props} />)
  return props
}

afterEach(() => {
  cleanup()
})

describe('EditorChatBar', () => {
  it('com o campo vazio o botão elabora', () => {
    const props = barra({ podeConversar: true })
    fireEvent.click(screen.getByRole('button', { name: 'Elaborar' }))
    expect(props.onElaborar).toHaveBeenCalledOnce()
    expect(props.onEnviarChat).not.toHaveBeenCalled()
  })

  it('com texto o mesmo botão envia a instrução', () => {
    const props = barra({ podeConversar: true, chatInput: 'Inclua preliminar' })
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }))
    expect(props.onEnviarChat).toHaveBeenCalledOnce()
    expect(props.onElaborar).not.toHaveBeenCalled()
  })

  it('enter com texto envia e não elabora', () => {
    const props = barra({ podeConversar: true, chatInput: 'Deixe mais formal' })
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' })
    expect(props.onEnviarChat).toHaveBeenCalledOnce()
    expect(props.onElaborar).not.toHaveBeenCalled()
  })

  it('antes do primeiro rascunho o campo fica fechado e o botão só elabora', () => {
    barra({ podeConversar: false, chatInput: 'texto antigo' })
    expect((screen.getByRole('textbox') as HTMLInputElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Elaborar' }) as HTMLButtonElement).disabled).toBe(
      false,
    )
    expect(screen.queryByRole('button', { name: 'Enviar' })).toBeNull()
  })
})

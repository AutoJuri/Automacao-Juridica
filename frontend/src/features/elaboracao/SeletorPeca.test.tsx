/** @vitest-environment jsdom */
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SeletorPeca } from './SeletorPeca'

afterEach(() => {
  cleanup()
})

describe('SeletorPeca', () => {
  it('sem sugestão não mostra o rótulo "Sugerido por IA"', () => {
    render(
      <SeletorPeca pecaSelecionada="contestacao" onChange={vi.fn()} sugestao={null} />,
    )

    expect(screen.queryByText('Sugerido por IA')).toBeNull()
  })

  it('com sugestão para a peça selecionada mostra rótulo e explicação', () => {
    render(
      <SeletorPeca
        pecaSelecionada="contestacao"
        onChange={vi.fn()}
        sugestao={{ peca: 'contestacao', explicacao: 'Encontrei "citação" na última intimação.' }}
      />,
    )

    expect(screen.getByText('Sugerido por IA')).toBeTruthy()
    expect(screen.getByText('Encontrei "citação" na última intimação.')).toBeTruthy()
  })

  it('sugestão para outra peça (não a selecionada) não mostra o rótulo', () => {
    render(
      <SeletorPeca
        pecaSelecionada="replica"
        onChange={vi.fn()}
        sugestao={{ peca: 'contestacao', explicacao: 'Sugestão para outra peça.' }}
      />,
    )

    expect(screen.queryByText('Sugerido por IA')).toBeNull()
  })

  it('sugestao com peca=null não mostra o rótulo', () => {
    render(
      <SeletorPeca
        pecaSelecionada="contestacao"
        onChange={vi.fn()}
        sugestao={{ peca: null, explicacao: null }}
      />,
    )

    expect(screen.queryByText('Sugerido por IA')).toBeNull()
  })
})

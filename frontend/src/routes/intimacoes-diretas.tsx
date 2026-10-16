import { createFileRoute, redirect } from '@tanstack/react-router'

/**
 * A tela continua em `features/intimacoes/IntimacoesDiretasPage.tsx`.
 * Fora do menu por enquanto: quem abre a URL volta para Andamentos.
 */
export const Route = createFileRoute('/intimacoes-diretas')({
  beforeLoad: () => {
    throw redirect({ to: '/' })
  },
})

/**
 * Navegação autenticada: áreas no topo e seções operacionais de Gerências.
 * Peticionamento, Custas DARE, Certidões e Validar Assinatura saíram do menu
 * de propósito — as rotas placeholder que ainda existem não voltam para cá.
 */
export const SIDEBAR_WIDTH = 80

export const SECOES_LATERAL = [
  { to: '/', label: 'Andamentos', icone: 'layers' },
  { to: '/consulta-pasta', label: 'Consultas', icone: 'search' },
  { to: '/pautas', label: 'Audiências', icone: 'calendar' },
  { to: '/push-robos', label: 'Push Robôs', icone: 'radio' },
] as const

export const SECOES_TOPO = [
  { to: '/', label: 'Gerências', icone: 'briefcase' },
  { to: '/elaboracoes', label: 'Elaborações', icone: 'pen' },
  { to: '/drive', label: 'Drive', icone: 'folder' },
  { to: '/tarefas', label: 'Tarefas', icone: 'check' },
] as const

export type SecaoLateralTo = (typeof SECOES_LATERAL)[number]['to']
export type SecaoTopoTo = (typeof SECOES_TOPO)[number]['to']
export type IconeLateral = (typeof SECOES_LATERAL)[number]['icone']
export type IconeTopo = (typeof SECOES_TOPO)[number]['icone']

const ROTAS_GERENCIAS = new Set<string>([
  '/',
  '/gerencias',
  ...SECOES_LATERAL.map((item) => item.to),
])

/** Rail e módulos operacionais só existem dentro de Gerências. */
export function estaEmGerencias(pathname: string): boolean {
  return ROTAS_GERENCIAS.has(pathname)
}

/** Gerências cobre Andamentos/Consultas/etc.; Elaborações cobre também a minuta. */
export function secaoTopoAtiva(to: SecaoTopoTo, pathname: string): boolean {
  if (to === '/') {
    return estaEmGerencias(pathname)
  }
  if (to === '/elaboracoes') {
    return pathname === '/elaboracoes' || pathname.startsWith('/elaboracao/')
  }
  return pathname === to
}

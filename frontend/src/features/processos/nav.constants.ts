/**
 * Seções da navbar autenticada. `/` é o painel real; as demais ainda são
 * placeholders até cada módulo existir.
 */
export const SECOES_NAV = [
  { to: '/', label: 'Autos & Gabinete' },
  { to: '/peticionamento', label: 'Peticionamento' },
  { to: '/consulta-pasta', label: 'Consulta / Pasta Digital' },
  { to: '/intimacoes-diretas', label: 'Intimações Diretas', badge: 'intimacoes' },
  { to: '/certidoes', label: 'Certidões' },
  { to: '/custas-dare', label: 'Custas DARE' },
  { to: '/pautas', label: 'Pautas' },
  { to: '/push-robos', label: 'Push Robôs' },
  { to: '/validar-assinatura', label: 'Validar Assinatura' },
] as const

export type SecaoNavTo = (typeof SECOES_NAV)[number]['to']

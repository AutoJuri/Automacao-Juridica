import { isAxiosError } from 'axios'

import { MUITAS_TENTATIVAS, mensagemDeErro } from '#/features/auth/auth.errors'

/** Status em que o backend do Drive devolve uma frase própria, já sem dado sensível. */
const STATUS_COM_DETALHE = [404, 409, 413, 422, 502]

/**
 * Mensagem para a tela. Usa o `detail` do servidor quando ele é uma frase curta
 * (as do Drive são escritas à mão); senão cai no texto por status.
 */
export function mensagemDoDrive(erro: unknown, extras: Record<number, string> = {}): string {
  if (isAxiosError(erro) && erro.response && STATUS_COM_DETALHE.includes(erro.response.status)) {
    const dados: unknown = erro.response.data
    const detalhe =
      typeof dados === 'object' && dados !== null && 'detail' in dados
        ? (dados as { detail: unknown }).detail
        : null
    if (typeof detalhe === 'string' && detalhe.length > 0 && detalhe.length <= 200) {
      return detalhe
    }
  }
  return mensagemDeErro(erro, {
    401: 'Sessão expirada. Entre novamente.',
    409: 'Conecte o Google Drive para continuar.',
    413: 'O arquivo passa de 25 MB.',
    429: MUITAS_TENTATIVAS,
    503: 'O Google Drive ainda não foi configurado neste servidor.',
    ...extras,
  })
}

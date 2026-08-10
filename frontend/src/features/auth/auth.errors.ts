/**
 * Tradução de erros HTTP em mensagens para o usuário.
 *
 * As mensagens são definidas aqui, no frontend — nunca interpolamos o corpo da
 * resposta na tela, para não repassar detalhe técnico do servidor ao usuário.
 */

import { isAxiosError } from 'axios'

const SEM_CONEXAO = 'Não foi possível falar com o servidor. Verifique sua conexão.'
const ERRO_GENERICO = 'Algo deu errado. Tente novamente em instantes.'

export const MUITAS_TENTATIVAS = 'Muitas tentativas. Aguarde alguns minutos e tente de novo.'

export function mensagemDeErro(erro: unknown, porStatus: Record<number, string>): string {
  if (!isAxiosError(erro)) {
    return ERRO_GENERICO
  }

  if (!erro.response) {
    return SEM_CONEXAO
  }

  return porStatus[erro.response.status] ?? ERRO_GENERICO
}

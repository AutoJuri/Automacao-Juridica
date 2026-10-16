import type { Coluna, Quadro, RascunhoTarefa, Tarefa } from './tarefas.types'

export const MAX_COLUNAS = 4
export const LIMITE_TITULO_COLUNA = 40
export const LIMITE_TITULO_TAREFA = 120
export const LIMITE_DESCRICAO = 2000

const PREFIXO_DROP_COLUNA = 'coluna:'

export const COLUNAS_PADRAO: readonly Coluna[] = [
  { id: 'a-fazer', titulo: 'A fazer', conclusao: false, total: 0 },
  { id: 'em-andamento', titulo: 'Em andamento', conclusao: false, total: 0 },
  { id: 'concluido', titulo: 'Concluído', conclusao: true, total: 0 },
]

export function quadroInicial(): Quadro {
  return {
    titulo: 'Tarefas',
    descricao: 'Suas tarefas. O responsável é você.',
    colunas: COLUNAS_PADRAO.map((coluna) => ({ ...coluna })),
    tarefas: [],
  }
}

export function idDropColuna(colunaId: string): string {
  return `${PREFIXO_DROP_COLUNA}${colunaId}`
}

export type TomDaColuna = 'fazer' | 'andamento' | 'conclusao'

/** A primeira coluna que não é de conclusão é "a fazer". As do meio são "andamento". */
export function tomDaColuna(colunas: readonly Coluna[], coluna: Coluna): TomDaColuna {
  if (coluna.conclusao) {
    return 'conclusao'
  }
  const primeira = colunas.find((item) => !item.conclusao)
  return primeira?.id === coluna.id ? 'fazer' : 'andamento'
}

export interface AtalhoColuna {
  id: string
  titulo: string
}

/**
 * Avançar vai para a coluna seguinte, menos quando ela já é a de conclusão.
 * Concluir salta direto para a coluna marcada, de qualquer lugar anterior.
 */
export function atalhosDaColuna(
  quadro: Quadro,
  colunaId: string,
): { avancar: AtalhoColuna | null; concluir: AtalhoColuna | null } {
  const indice = quadro.colunas.findIndex((coluna) => coluna.id === colunaId)
  if (indice < 0) {
    return { avancar: null, concluir: null }
  }
  const seguinte = quadro.colunas[indice + 1]
  const conclusao = quadro.colunas.find((coluna) => coluna.conclusao)
  return {
    avancar: seguinte && !seguinte.conclusao ? { id: seguinte.id, titulo: seguinte.titulo } : null,
    concluir: conclusao && conclusao.id !== colunaId ? { id: conclusao.id, titulo: conclusao.titulo } : null,
  }
}

export function tarefasDaColuna(quadro: Quadro, colunaId: string): Tarefa[] {
  return quadro.tarefas.filter((tarefa) => tarefa.colunaId === colunaId)
}

/** Atualiza o contador quando o card muda de coluna, antes da resposta do servidor. */
export function ajustarTotais(quadro: Quadro, colunaOrigemId: string, colunaDestinoId: string): Quadro {
  if (colunaOrigemId === colunaDestinoId) {
    return quadro
  }
  return {
    ...quadro,
    colunas: quadro.colunas.map((coluna) => {
      if (coluna.id === colunaOrigemId) {
        return { ...coluna, total: Math.max(0, coluna.total - 1) }
      }
      if (coluna.id === colunaDestinoId) {
        return { ...coluna, total: coluna.total + 1 }
      }
      return coluna
    }),
  }
}

/** Acrescenta a próxima leva da coluna de conclusão sem repetir card já visível. */
export function incluirPagina(quadro: Quadro, colunaId: string, tarefas: Tarefa[], total: number): Quadro {
  const ids = new Set(quadro.tarefas.map((tarefa) => tarefa.id))
  const extras = tarefas.filter((tarefa) => !ids.has(tarefa.id))
  return {
    ...quadro,
    colunas: quadro.colunas.map((coluna) => (coluna.id === colunaId ? { ...coluna, total } : coluna)),
    tarefas: [...quadro.tarefas, ...extras],
  }
}

export function adicionarColuna(quadro: Quadro, titulo: string, id: string): Quadro {
  if (quadro.colunas.length >= MAX_COLUNAS) {
    return quadro
  }
  const nome = textoLimitado(titulo, LIMITE_TITULO_COLUNA) || 'Nova coluna'
  return {
    ...quadro,
    colunas: [...quadro.colunas, { id, titulo: nome, conclusao: false, total: 0 }],
  }
}

export function renomearColuna(quadro: Quadro, colunaId: string, titulo: string): Quadro {
  const nome = textoLimitado(titulo, LIMITE_TITULO_COLUNA)
  if (!nome) {
    return quadro
  }
  const coluna = quadro.colunas.find((item) => item.id === colunaId)
  if (!coluna || coluna.titulo === nome) {
    return quadro
  }
  return {
    ...quadro,
    colunas: quadro.colunas.map((item) => (item.id === colunaId ? { ...item, titulo: nome } : item)),
  }
}

/** Remove só coluna vazia, e nunca a última do quadro. */
export function removerColuna(quadro: Quadro, colunaId: string): Quadro {
  if (quadro.colunas.length <= 1) {
    return quadro
  }
  if (quadro.tarefas.some((tarefa) => tarefa.colunaId === colunaId)) {
    return quadro
  }
  if (!quadro.colunas.some((coluna) => coluna.id === colunaId)) {
    return quadro
  }
  return {
    ...quadro,
    colunas: quadro.colunas.filter((coluna) => coluna.id !== colunaId),
  }
}

/**
 * Reordena na mesma coluna ou move para outra.
 * `sobreId` é o id de uma tarefa ou o id de drop da coluna (`coluna:{id}`).
 */
export function moverTarefa(quadro: Quadro, ativaId: string, sobreId: string): Quadro {
  if (!sobreId || ativaId === sobreId) {
    return quadro
  }
  const origem = quadro.tarefas.findIndex((tarefa) => tarefa.id === ativaId)
  if (origem < 0) {
    return quadro
  }
  const ativa = quadro.tarefas[origem]
  const colunaDestino = colunaDoDrop(sobreId) ?? colunaDireta(quadro, sobreId)
  if (colunaDestino) {
    if (!quadro.colunas.some((coluna) => coluna.id === colunaDestino)) {
      return quadro
    }
    return inserirNaColuna(quadro, ativa, colunaDestino, null)
  }
  const sobre = quadro.tarefas.find((tarefa) => tarefa.id === sobreId)
  if (!sobre) {
    return quadro
  }
  if (ativa.colunaId === sobre.colunaId) {
    const destino = quadro.tarefas.findIndex((tarefa) => tarefa.id === sobreId)
    return { ...quadro, tarefas: arrayMove(quadro.tarefas, origem, destino) }
  }
  return inserirNaColuna(quadro, ativa, sobre.colunaId, sobre.id)
}

export function validarRascunho(rascunho: RascunhoTarefa): string | null {
  const titulo = rascunho.titulo.trim()
  if (!titulo) {
    return 'Informe o título da tarefa.'
  }
  if (titulo.length > LIMITE_TITULO_TAREFA) {
    return `O título pode ter no máximo ${LIMITE_TITULO_TAREFA} caracteres.`
  }
  if (rascunho.descricao.trim().length > LIMITE_DESCRICAO) {
    return `A descrição pode ter no máximo ${LIMITE_DESCRICAO} caracteres.`
  }
  if (!rascunho.responsavelId) {
    return 'Escolha quem vai fazer a tarefa.'
  }
  if (rascunho.prazo && !/^\d{4}-\d{2}-\d{2}$/.test(rascunho.prazo)) {
    return 'Prazo inválido.'
  }
  return null
}

export function materializarTarefa(
  rascunho: RascunhoTarefa,
  colunaId: string,
  id: string,
): Tarefa {
  return {
    id,
    colunaId,
    titulo: textoLimitado(rascunho.titulo, LIMITE_TITULO_TAREFA),
    descricao: rascunho.descricao.trim().slice(0, LIMITE_DESCRICAO),
    responsavelId: rascunho.responsavelId,
    processoId: rascunho.processoId,
    prazo: rascunho.prazo,
  }
}

/** Vencida quando a data é anterior a hoje em America/Sao_Paulo. O dia de hoje ainda vale. */
export function estaAtrasada(prazo: string | null, hoje: string = hojeEmSaoPaulo()): boolean {
  if (!prazo || !/^\d{4}-\d{2}-\d{2}$/.test(prazo)) {
    return false
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(hoje)) {
    return false
  }
  return prazo < hoje
}

export function hojeEmSaoPaulo(agora: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(agora)
}

export function textoLimitado(valor: string, max: number): string {
  return valor.trim().slice(0, max)
}

function colunaDoDrop(sobreId: string): string | null {
  if (!sobreId.startsWith(PREFIXO_DROP_COLUNA)) {
    return null
  }
  const colunaId = sobreId.slice(PREFIXO_DROP_COLUNA.length)
  return colunaId || null
}

function colunaDireta(quadro: Quadro, sobreId: string): string | null {
  return quadro.colunas.some((coluna) => coluna.id === sobreId) ? sobreId : null
}

function inserirNaColuna(
  quadro: Quadro,
  ativa: Tarefa,
  colunaId: string,
  antesDeId: string | null,
): Quadro {
  const resto = quadro.tarefas.filter((tarefa) => tarefa.id !== ativa.id)
  const movida: Tarefa = { ...ativa, colunaId }
  let indice = resto.length
  if (antesDeId) {
    const encontrado = resto.findIndex((tarefa) => tarefa.id === antesDeId)
    if (encontrado >= 0) {
      indice = encontrado
    }
  } else {
    for (let i = resto.length - 1; i >= 0; i -= 1) {
      if (resto[i].colunaId === colunaId) {
        indice = i + 1
        break
      }
    }
  }
  const tarefas = [...resto]
  tarefas.splice(indice, 0, movida)
  return { ...quadro, tarefas }
}

function arrayMove<T>(lista: readonly T[], de: number, para: number): T[] {
  const proxima = lista.slice()
  const [item] = proxima.splice(de, 1)
  proxima.splice(para, 0, item)
  return proxima
}

import type { ProcessoPortalKey } from './portais.mock'

export type TribunalKey = 'TJSP' | 'TRF3' | 'STJ'

export interface Processo {
  id: number
  tribunal: TribunalKey
  tribunalColor: string
  /** Portal de origem do processo (e-SAJ, PJe, etc.). */
  portal: ProcessoPortalKey
  numero: string
  cliente: string
  /** Data de início do prazo (DD/MM/YYYY) — usada para calcular urgência. */
  prazoInicio: string
  /** Data limite do prazo (DD/MM/YYYY) — exibida no card. */
  prazoFim: string
  /** Data em que ocorreu a última movimentação (DD/MM/YYYY). */
  dataUltimaAlteracao: string
  ultimaAlteracao: string
  /** Ação sugerida com base no estágio processual atual. */
  proximoPasso: string
  ativo: boolean
  classeJudicial: string
  assunto: string
  magistrado: string
  ultimaAtualizacaoTecnica: string
  /** Resumo do objeto/causa da ação exibido no cabeçalho do detalhe. */
  objetoAcao: string
}

export interface Movimentacao {
  id: number
  processoId: number
  /** Data exata do andamento no tribunal (DD/MM/YYYY). */
  data: string
  /** Nome real da etapa conforme consta no andamento do e-SAJ. */
  nomeEtapa: string
  /** Descrição literal do andamento no site do tribunal. */
  descricao: string
}

export interface Documento {
  id: number
  processoId: number
  titulo: string
  subtitulo: string
  conteudo: string
  origem: string
  paginas: string
}

export const processosMockados: Processo[] = [
  {
    id: 1,
    tribunal: 'TJSP',
    tribunalColor: '#3B5BDB',
    portal: 'esaj_tjsp',
    numero: '1002561-84.2026.8.26.0100',
    cliente: 'Acme Industrial Brasil S.A.',
    prazoInicio: '28/05/2026',
    prazoFim: '05/06/2026',
    dataUltimaAlteracao: '28/05/2026',
    ultimaAlteracao:
      'Remetidos os autos ao Ministério Público com urgência legal extrema',
    proximoPasso: 'Montar a contestação',
    ativo: true,
    classeJudicial: 'PROCEDIMENTO COMUM CÍVEL',
    assunto: 'Tutela de Urgência / Liminar Automotiva',
    magistrado: 'Dr. Alexandre de Oliveira Marcondes',
    ultimaAtualizacaoTecnica: '28/05/2026',
    objetoAcao:
      'Tutela de urgência para restrição de transferência de veículo perante o DETRAN/SP',
  },
  {
    id: 2,
    tribunal: 'TRF3',
    tribunalColor: '#F97316',
    portal: 'pje_trf3',
    numero: '5001429-12.2026.4.03.6100',
    cliente: 'Carlos Eduardo da Silva Prado',
    prazoInicio: '25/05/2026',
    prazoFim: '25/07/2026',
    dataUltimaAlteracao: '25/05/2026',
    ultimaAlteracao:
      'Ato ordinatório praticado - Vista ao autor para manifestação sobre contestação da autarquia federal',
    proximoPasso: 'Manifestar sobre a contestação da autarquia federal',
    ativo: false,
    classeJudicial: 'MANDADO DE SEGURANÇA',
    assunto: 'Ato Administrativo / Servidor Público Federal',
    magistrado: 'Dra. Patrícia Andrade Freitas',
    ultimaAtualizacaoTecnica: '25/05/2026',
    objetoAcao:
      'Anulação de ato administrativo que negou progressão funcional de servidor público federal',
  },
]

export const movimentacoesMockadas: Movimentacao[] = [
  {
    id: 1,
    processoId: 1,
    data: '28/05/2026',
    nomeEtapa: 'Remessa ao MP',
    descricao: 'Remetidos os Autos ao Ministério Público',
  },
  {
    id: 2,
    processoId: 1,
    data: '25/05/2026',
    nomeEtapa: 'Decisão Interlocutória',
    descricao:
      'Proferido despacho de mero expediente - Determinada a averbação de restrição de transferência perante o DETRAN/SP no prazo de 24 horas',
  },
  {
    id: 3,
    processoId: 1,
    data: '15/05/2026',
    nomeEtapa: 'Petição Inicial',
    descricao: 'Petição inicial protocolada',
  },
  {
    id: 4,
    processoId: 2,
    data: '25/05/2026',
    nomeEtapa: 'Ato Ordinatório',
    descricao:
      'Publicado Ato Ordinatório em 25/05/2026 - Vista ao autor para manifestação sobre contestação da autarquia federal',
  },
  {
    id: 5,
    processoId: 2,
    data: '10/05/2026',
    nomeEtapa: 'Distribuição',
    descricao: 'Distribuído por sorteio',
  },
]

export const documentosMockados: Documento[] = [
  {
    id: 1,
    processoId: 1,
    titulo: 'CERTIFICADO DIGITAL OFICIAL — PK/175',
    subtitulo: 'TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\nFORO CENTRAL CÍVEL — SÃO PAULO/SP',
    conteudo: `TERMO DE REMESSA DE AUTOS EXTRAORDINÁRIO
PROCESSO Nº 1002561-84.2026.8.26.0100

Aos 28/05/2026, faço remessa destes autos digitais ao Excelentíssimo Senhor Promotor de Justiça, conforme despacho deste juízo com caráter de urgência legal extrema determinada por decisão judicial anterior.

Objeto: Manifestação acerca de tutela provisória de urgência em M.P.

Certifico e dou fé.`,
    origem: 'Autr. Digitado — TJSP',
    paginas: 'Caracteres: 426',
  },
  {
    id: 2,
    processoId: 1,
    titulo: 'DESPACHO INTERLOCUTÓRIO — FL/089',
    subtitulo: 'TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\nFORO CENTRAL CÍVEL — SÃO PAULO/SP',
    conteudo: `DESPACHO

Vistos.

Determino a averbação de restrição de transferência perante o DETRAN/SP, a ser cumprida no prazo improrrogável de 24 (vinte e quatro) horas, sob pena de expedição de mandado de busca e apreensão do veículo.

Intime-se o requerido e dê-se ciência ao Ministério Público.

São Paulo, 25 de maio de 2026.

Dr. Alexandre de Oliveira Marcondes
Juiz de Direito — 3ª Vara Cível`,
    origem: 'Autr. Digitado — TJSP',
    paginas: 'Caracteres: 512',
  },
  {
    id: 3,
    processoId: 2,
    titulo: 'MANDADO DE SEGURANÇA — IMPETRAÇÃO',
    subtitulo: 'TRIBUNAL REGIONAL FEDERAL — 3ª REGIÃO\nSEÇÃO JUDICIÁRIA DE SÃO PAULO',
    conteudo: `MANDADO DE SEGURANÇA Nº 5001429-12.2026.4.03.6100

Impetrante: Carlos Eduardo da Silva Prado
Impetrado: Diretor de Recursos Humanos — INSS

Objeto: Ato administrativo que negou progressão funcional sem motivação expressa, em violação ao art. 37 da CF/88 e ao princípio da motivação dos atos administrativos.

Requer liminar inaudita altera parte.`,
    origem: 'Autr. Digitado — TRF3',
    paginas: 'Caracteres: 398',
  },
]

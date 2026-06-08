export type TribunalKey = 'TJSP' | 'TRF3' | 'STJ'
export type PrazoKey = 'PRAZO CRÍTICO' | 'PRAZO MÉDIO' | 'PRAZO NORMAL' | 'SEM PRAZO'

export interface Processo {
  id: number
  tribunal: TribunalKey
  tribunalColor: string
  numero: string
  cliente: string
  prazo: PrazoKey
  prazoColor: string
  ultimaAlteracao: string
  ativo: boolean
  classeJudicial: string
  assunto: string
  magistrado: string
  ultimaAtualizacaoTecnica: string
}

export interface Movimentacao {
  id: number
  processoId: number
  data: string
  fase: string
  descricao: string
  tipo: string
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
    numero: '1002561-84.2026.8.26.0100',
    cliente: 'Acme Industrial Brasil S.A.',
    prazo: 'PRAZO CRÍTICO',
    prazoColor: '#EF4444',
    ultimaAlteracao:
      'Remetidos os autos ao Ministério Público com urgência legal extrema',
    ativo: true,
    classeJudicial: 'PROCEDIMENTO COMUM CÍVEL',
    assunto: 'Tutela de Urgência / Liminar Automotiva',
    magistrado: 'Dr. Alexandre de Oliveira Marcondes',
    ultimaAtualizacaoTecnica: '28/05/2026',
  },
  {
    id: 2,
    tribunal: 'TRF3',
    tribunalColor: '#F97316',
    numero: '5001429-12.2026.4.03.6100',
    cliente: 'Carlos Eduardo da Silva Prado',
    prazo: 'PRAZO MÉDIO',
    prazoColor: '#F59E0B',
    ultimaAlteracao:
      'Ato ordinatório praticado - Vista ao autor para manifestação sobre contestação da autarquia federal',
    ativo: false,
    classeJudicial: 'MANDADO DE SEGURANÇA',
    assunto: 'Ato Administrativo / Servidor Público Federal',
    magistrado: 'Dra. Patrícia Andrade Freitas',
    ultimaAtualizacaoTecnica: '25/05/2026',
  },
]

export const movimentacoesMockadas: Movimentacao[] = [
  {
    id: 1,
    processoId: 1,
    data: '28/05/2026',
    fase: 'FASE 3',
    descricao:
      'Remetidos os autos ao Ministério Público com urgência legal extrema',
    tipo: 'Remessa',
  },
  {
    id: 2,
    processoId: 1,
    data: '25/05/2026',
    fase: 'FASE 2',
    descricao:
      'Decisão proferida ou despacho interlocutório - Determinada a averbação de restrição parante a Detran no prazo de 24 horas sob pena de busca e apreensão',
    tipo: 'Decisão',
  },
  {
    id: 3,
    processoId: 1,
    data: '15/05/2026',
    fase: 'FASE 1',
    descricao: 'Petição Inicial protocolada',
    tipo: 'Petição',
  },
  {
    id: 4,
    processoId: 2,
    data: '25/05/2026',
    fase: 'FASE 2',
    descricao:
      'Ato ordinatório praticado - Vista ao autor para manifestação sobre contestação da autarquia federal',
    tipo: 'Ato Ordinatório',
  },
  {
    id: 5,
    processoId: 2,
    data: '10/05/2026',
    fase: 'FASE 1',
    descricao: 'Impetração do Mandado de Segurança distribuída por sorteio',
    tipo: 'Distribuição',
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

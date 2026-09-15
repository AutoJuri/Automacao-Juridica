export interface ModeloPeca {
  id: string
  nome: string
  grupo: string
}

export interface JulgadoIlustrativo {
  id: string
  titulo: string
  tribunal: string
  resumo: string
  categoria: 'tribunais' | 'decisoes' | 'sumulas' | 'leis'
}

export const modelosPeca: ModeloPeca[] = [
  { id: 'contestacao', nome: 'Contestação', grupo: 'Defesa' },
  { id: 'replica', nome: 'Réplica', grupo: 'Defesa' },
  { id: 'recurso_inominado', nome: 'Recurso Inominado', grupo: 'Recursos' },
  { id: 'apelacao', nome: 'Apelação', grupo: 'Recursos' },
  { id: 'agravo_interno', nome: 'Agravo Interno', grupo: 'Recursos' },
  { id: 'memoriais', nome: 'Memoriais', grupo: 'Outros' },
  { id: 'peticao_inicial', nome: 'Petição Inicial', grupo: 'Inicial' },
  { id: 'tutela_urgencia', nome: 'Tutela de Urgência', grupo: 'Urgência' },
  { id: 'impugnacao_contestacao', nome: 'Impugnação à Contestação', grupo: 'Defesa' },
  { id: 'embargos_declaracao', nome: 'Embargos de Declaração', grupo: 'Recursos' },
]

/** Só visual — não vem do e-SAJ nem de base oficial. */
export const JULGADOS_ILUSTRATIVOS: JulgadoIlustrativo[] = [
  {
    id: 'j1',
    titulo: 'Apelação cível — responsabilidade civil',
    tribunal: 'TJSP',
    resumo: 'Julgado ilustrativo. Não usar como fundamento real.',
    categoria: 'tribunais',
  },
  {
    id: 'j2',
    titulo: 'REsp — manutenção indevida de restrição',
    tribunal: 'STJ',
    resumo: 'Card fictício para o layout de jurisprudência.',
    categoria: 'decisoes',
  },
  {
    id: 'j3',
    titulo: 'Súmula — ônus da prova',
    tribunal: 'STJ',
    resumo: 'Entrada ilustrativa de súmula. Sem texto oficial.',
    categoria: 'sumulas',
  },
  {
    id: 'j4',
    titulo: 'CPC/2015, art. 335',
    tribunal: 'Lei',
    resumo: 'Referência visual ao prazo de contestação. Sem citação completa.',
    categoria: 'leis',
  },
]

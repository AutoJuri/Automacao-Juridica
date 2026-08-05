export interface ModeloPeca {
  id: string
  nome: string
  grupo: string
}

export interface VersaoPeca {
  id: number
  rotulo: string
  horario: string
  ativa: boolean
}

export interface RequisitoCompletude {
  id: string
  descricao: string
  atendido: boolean
}

export interface JurisprudenciaToggle {
  id: string
  label: string
  sublabel?: string
  ativo: boolean
  categoria: 'tribunal' | 'fonte' | 'autor'
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

export const versoesMock: VersaoPeca[] = [
  { id: 3, rotulo: 'Versão 3', horario: '01:12', ativa: true },
  { id: 2, rotulo: 'Versão 2', horario: '00:48', ativa: false },
  { id: 1, rotulo: 'Versão 1', horario: '00:21', ativa: false },
]

export const requisitosCompletude: RequisitoCompletude[] = [
  { id: 'valor_causa', descricao: 'Valor da causa indicado', atendido: true },
  { id: 'qualificacao_autor', descricao: 'Qualificação do autor completa', atendido: true },
  { id: 'qualificacao_reu', descricao: 'Qualificação do réu completa', atendido: true },
  { id: 'fatos', descricao: 'Narração dos fatos', atendido: true },
  { id: 'fundamentos', descricao: 'Fundamentos jurídicos', atendido: true },
  { id: 'preliminares', descricao: 'Preliminares de defesa', atendido: true },
  { id: 'pedidos', descricao: 'Pedidos finais discriminados', atendido: false },
  { id: 'protestos', descricao: 'Protestos finais', atendido: false },
  { id: 'provas', descricao: 'Especificação de provas', atendido: false },
  { id: 'docs_anexos', descricao: 'Documentos comprobatórios listados', atendido: false },
]

export const jurisprudenciaToggles: JurisprudenciaToggle[] = [
  { id: 'stj', label: 'STJ', sublabel: 'Superior Tribunal de Justiça', ativo: true, categoria: 'tribunal' },
  { id: 'stf', label: 'STF', sublabel: 'Supremo Tribunal Federal', ativo: false, categoria: 'tribunal' },
  { id: 'tjsp', label: 'TJSP', sublabel: 'Tribunal de Justiça — SP', ativo: true, categoria: 'tribunal' },
  { id: 'trf3', label: 'TRF3', sublabel: '3ª Região Federal', ativo: false, categoria: 'tribunal' },
  { id: 'sumulas', label: 'Súmulas', sublabel: 'Súmulas vinculantes e normativas', ativo: true, categoria: 'fonte' },
  { id: 'decisoes', label: 'Decisões Recentes', sublabel: 'Últimos 12 meses', ativo: false, categoria: 'fonte' },
  { id: 'doutrina', label: 'Doutrina', sublabel: 'Obras jurídicas referenciadas', ativo: false, categoria: 'fonte' },
  { id: 'leis', label: 'Legislação', sublabel: 'CPC, CC, CF/88 e legislação esparsa', ativo: true, categoria: 'fonte' },
]

export const PERCENTUAL_COMPLETUDE = 60

export const textoContestacaoMock = `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 3ª VARA CÍVEL DO FORO CENTRAL DA COMARCA DA CAPITAL DO ESTADO DE SÃO PAULO

Processo nº 1002561-84.2026.8.26.0100

ACME INDUSTRIAL BRASIL S.A., pessoa jurídica de direito privado, inscrita no CNPJ/MF sob o nº 12.345.678/0001-90, com sede na Avenida Paulista, nº 1.000, Bela Vista, São Paulo/SP, CEP 01310-100, por seus advogados que esta subscrevem (procuração inclusa — doc. 01), vem, respeitosamente, à presença de Vossa Excelência, com fundamento nos artigos 335 e seguintes do Código de Processo Civil, apresentar

CONTESTAÇÃO

em face da ação de tutela de urgência proposta por BANCO MERIDIONAL S.A., pelos fatos e fundamentos a seguir expostos.

I — DOS FATOS

A requerente ingressou com a presente ação pleiteando a restrição de transferência do veículo de placa ABC-1D23 junto ao DETRAN/SP, sob o argumento de existência de garantia fiduciária em seu favor.

Todavia, conforme documentos em anexo (docs. 02 a 05), o contrato de alienação fiduciária já foi integralmente quitado em 14/03/2026, tendo a requerente emitido Carta de Quitação naquela data, sem jamais proceder ao cancelamento da restrição junto ao órgão competente.

A conduta omissiva da requerente causou à contestante prejuízos materiais decorrentes da impossibilidade de alienação do veículo, culminando na perda de negócio de venda no valor de R$ 48.000,00 (quarenta e oito mil reais), conforme proposta de compra e venda juntada (doc. 06).

II — DO DIREITO

Conforme entendimento pacificado no Superior Tribunal de Justiça ¹, a instituição financeira que mantém indevida restrição sobre bem alienado fiduciariamente após a quitação integral do débito responde pelos danos materiais e morais daí decorrentes, nos termos do art. 927 do Código Civil.

Ademais, o art. 2º da Lei nº 9.514/1997, que regula a alienação fiduciária de bens móveis no âmbito do Sistema de Financiamento Imobiliário, bem como o art. 1.361 do Código Civil, são expressos ao impor ao credor fiduciário o dever de baixar a restrição no prazo de cinco dias úteis após a quitação.

Neste mesmo sentido manifestou-se recentemente o TJSP ², ao julgar caso análogo envolvendo manutenção indevida de gravame em veículo já quitado.

III — DAS PRELIMINARES

3.1. AUSÊNCIA DE FUMUS BONI IURIS

Não restam demonstrados os requisitos autorizadores da tutela de urgência previstos no art. 300 do CPC/2015, especialmente a probabilidade do direito, haja vista que os documentos apresentados pela requerente são contraditórios com os registros internos da própria instituição financeira.

3.2. AUSÊNCIA DE PERICULUM IN MORA

Tampouco se verifica o perigo de dano ou risco ao resultado útil do processo, na medida em que o veículo permanece regularmente registrado e em poder da contestante, sem qualquer indício de dilapidação patrimonial.

IV — DO MÉRITO

[continua...]`

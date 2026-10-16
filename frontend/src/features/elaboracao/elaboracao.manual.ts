import type { ProcessoDetalhe } from '#/features/processos/processos.types'

import type { ElaboracaoDetalhe } from './elaboracoes.types'

export interface CamposManuais {
  nu_processo: string
  parte_ativa: string
  parte_passiva: string
  foro_vara: string
  valor_causa: string
}

export const CAMPOS_MANUAIS_VAZIOS: CamposManuais = {
  nu_processo: '',
  parte_ativa: '',
  parte_passiva: '',
  foro_vara: '',
  valor_causa: '',
}

export function camposDeCapa(capa: ElaboracaoDetalhe): CamposManuais {
  return {
    nu_processo: capa.manual?.nu_processo ?? '',
    parte_ativa: capa.manual?.parte_ativa ?? '',
    parte_passiva: capa.manual?.parte_passiva ?? '',
    foro_vara: capa.manual?.foro_vara ?? '',
    valor_causa: capa.manual?.valor_causa ?? '',
  }
}

export function capaComCampos(capa: ElaboracaoDetalhe, campos: CamposManuais): ElaboracaoDetalhe {
  const numero = campos.nu_processo.trim()
  const autor = campos.parte_ativa.trim()
  const reu = campos.parte_passiva.trim()
  const foro = campos.foro_vara.trim()
  const valor = campos.valor_causa.trim()
  return {
    ...capa,
    nu_processo: numero || null,
    autor: autor || null,
    reu: reu || null,
    manual: {
      titulo: capa.manual?.titulo?.trim() || capa.rotulo,
      nu_processo: numero || null,
      parte_ativa: autor || null,
      parte_passiva: reu || null,
      classe: capa.manual?.classe ?? null,
      assunto: capa.manual?.assunto ?? null,
      foro_vara: foro || null,
      valor_causa: valor || null,
      juiz: capa.manual?.juiz ?? null,
    },
  }
}

function parte(nome: string | null | undefined) {
  const texto = nome?.trim()
  if (!texto) {
    return null
  }
  return { nome: texto, representada: null }
}

/** Monta o formato que os painéis da minuta já conhecem, sem listas do e-SAJ. */
export function processoDeDadosManuais(capa: ElaboracaoDetalhe): ProcessoDetalhe {
  const manual = capa.manual
  return {
    id: capa.id,
    tribunal: '',
    nu_processo: manual?.nu_processo ?? null,
    de_classe: manual?.classe ?? null,
    de_assunto: manual?.assunto ?? null,
    instancia: null,
    parte_ativa: parte(manual?.parte_ativa),
    parte_passiva: parte(manual?.parte_passiva),
    last_synced_at: null,
    ultima_atividade: null,
    fixado: false,
    url_cpo: null,
    url_pasta: null,
    foro: manual?.foro_vara ?? null,
    vara: null,
    juiz: manual?.juiz ?? null,
    distribuicao: null,
    controle: null,
    area: null,
    valor_acao: manual?.valor_causa ?? null,
    partes_cpo: [],
    intimacoes: [],
    audiencias: [],
    movimentacoes: [],
    peticoes_diversas: [],
    audiencias_cpo: [],
    movimentacoes_status: 'indisponivel',
    sem_incidentes: true,
    sem_apensos: true,
    datajud: null,
  }
}

/** Folha A4 com a margem padrão do Word (2,54 cm). */
export const FOLHA_A4 = {
  larguraMm: 210,
  alturaMm: 297,
  margemMm: 25.4,
  vaoPx: 20,
}

export interface LinhaFolha {
  pos: number
  altura: number
  forcarQuebra: boolean
}

export interface QuebraFolha {
  pos: number
  restante: number
}

export interface DistribuicaoFolhas {
  quebras: QuebraFolha[]
  paginas: number
  sobra: number
}

/** Converte milímetros de CSS (96 px por polegada) para pixels. */
export function pxDeMm(mm: number): number {
  return (mm / 25.4) * 96
}

export function alturaUtilDaFolha(larguraPx: number, margemSuperiorPx: number, margemInferiorPx: number): number {
  const alturaFolha = larguraPx * (FOLHA_A4.alturaMm / FOLHA_A4.larguraMm)
  return Math.max(0, alturaFolha - margemSuperiorPx - margemInferiorPx)
}

/**
 * Reparte linhas numa sequência de folhas do mesmo tamanho.
 * `quebras` são as posições do documento onde começa uma folha nova.
 */
export function distribuirEmFolhas(linhas: LinhaFolha[], alturaUtil: number): DistribuicaoFolhas {
  const limite = Math.max(alturaUtil, 1)
  let usado = 0
  let paginas = 1
  const quebras: QuebraFolha[] = []

  const jaQuebrou = (pos: number) => quebras.some((quebra) => quebra.pos === pos)

  for (const linha of linhas) {
    if (linha.forcarQuebra) {
      if (!jaQuebrou(linha.pos)) {
        quebras.push({ pos: linha.pos, restante: Math.max(0, limite - usado) })
        paginas += 1
      }
      usado = 0
      continue
    }
    if (linha.altura <= 0) {
      continue
    }
    const naoCabe = usado > 0 && usado + linha.altura > limite + 0.5
    if (naoCabe && !jaQuebrou(linha.pos)) {
      quebras.push({ pos: linha.pos, restante: Math.max(0, limite - usado) })
      paginas += 1
      usado = linha.altura
      continue
    }
    usado += linha.altura
  }

  return {
    quebras,
    paginas,
    sobra: Math.max(0, limite - usado),
  }
}

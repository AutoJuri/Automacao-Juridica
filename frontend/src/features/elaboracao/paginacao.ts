import { Extension, Node } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'
import type { EditorView } from '@tiptap/pm/view'
import type { Node as ProseNode } from '@tiptap/pm/model'

import { FOLHA_A4, distribuirEmFolhas, type LinhaFolha } from './elaboracao.folhas'

const chavePaginacao = new PluginKey<{ deco: DecorationSet; paginas: number }>('paginacaoMinuta')

export const QuebraDePagina = Node.create({
  name: 'quebraDePagina',
  group: 'block',
  atom: true,
  selectable: true,

  parseHTML() {
    return [{ tag: 'div[data-quebra-pagina]' }]
  },

  renderHTML() {
    return ['div', { 'data-quebra-pagina': 'true', class: 'quebra-pagina' }]
  },

  addKeyboardShortcuts() {
    return {
      'Mod-Enter': () => {
        if (!this.editor.isEditable) {
          return false
        }
        return this.editor.chain().focus().insertContent({ type: this.name }).run()
      },
    }
  },
})

function margem(elemento: HTMLElement, lado: 'top' | 'bottom' | 'left'): number {
  const valor = Number.parseFloat(getComputedStyle(elemento).getPropertyValue(`padding-${lado}`))
  return Number.isFinite(valor) ? valor : 0
}

function posDaLinha(view: EditorView, no: Text, topo: number): number | null {
  const texto = no.textContent ?? ''
  if (!texto) {
    return null
  }
  let inicio = 0
  let fim = texto.length
  while (inicio < fim) {
    const meio = Math.floor((inicio + fim) / 2)
    const faixa = document.createRange()
    faixa.setStart(no, meio)
    faixa.setEnd(no, Math.min(texto.length, meio + 1))
    const rect = faixa.getBoundingClientRect()
    if (rect.height > 0 && rect.top < topo - 1) {
      inicio = meio + 1
      continue
    }
    fim = meio
  }
  const pos = view.posAtDOM(no, inicio)
  return pos >= 0 ? pos : null
}

function linhasDoBloco(view: EditorView, node: ProseNode, pos: number): LinhaFolha[] {
  if (node.type.name === 'quebraDePagina') {
    return [{ pos, altura: 0, forcarQuebra: true }]
  }
  const dom = view.nodeDOM(pos)
  if (!(dom instanceof HTMLElement)) {
    return []
  }
  const estilo = getComputedStyle(dom)
  const margemBaixo = Number.parseFloat(estilo.marginBottom) || 0
  const alturaSemFolha = () => {
    if (dom.querySelector('.folha-intervalo, .folha-sobra')) {
      const fonte = Number.parseFloat(estilo.fontSize) || 16
      const bruto = estilo.lineHeight
      const linha = bruto.endsWith('px') ? Number.parseFloat(bruto) : fonte * (Number.parseFloat(bruto) || 1.5)
      return (Number.isFinite(linha) ? linha : fonte * 1.5) + margemBaixo
    }
    return dom.getBoundingClientRect().height + margemBaixo
  }
  if (!dom.textContent?.trim()) {
    return [{ pos: pos + 1, altura: alturaSemFolha(), forcarQuebra: false }]
  }

  const fonte = Number.parseFloat(estilo.fontSize) || 16
  const bruto = estilo.lineHeight
  const linhaCss = bruto.endsWith('px') ? Number.parseFloat(bruto) : fonte * (Number.parseFloat(bruto) || 1.5)
  const alturaLinha = Number.isFinite(linhaCss) && linhaCss > 0 ? linhaCss : fonte * 1.5
  const grupos: { top: number; pos: number }[] = []
  const walker = document.createTreeWalker(dom, NodeFilter.SHOW_TEXT)
  let texto: globalThis.Node | null = walker.nextNode()
  while (texto) {
    const faixa = document.createRange()
    faixa.selectNodeContents(texto)
    for (const rect of faixa.getClientRects()) {
      if (rect.height <= 0 || rect.width <= 0) {
        continue
      }
      if (!(texto instanceof Text)) {
        continue
      }
      const pos = posDaLinha(view, texto, rect.top)
      if (pos == null) {
        continue
      }
      const ultimo = grupos[grupos.length - 1]
      if (ultimo && Math.abs(ultimo.top - rect.top) < 2) {
        ultimo.pos = Math.min(ultimo.pos, pos)
        continue
      }
      grupos.push({ top: rect.top, pos })
    }
    texto = walker.nextNode()
  }

  if (grupos.length === 0) {
    return [{ pos: pos + 1, altura: alturaSemFolha(), forcarQuebra: false }]
  }
  grupos.sort((a, b) => a.top - b.top)
  const linhasDoTexto: { top: number; pos: number }[] = []
  for (const grupo of grupos) {
    const ultimo = linhasDoTexto[linhasDoTexto.length - 1]
    if (ultimo && Math.abs(ultimo.top - grupo.top) < 2) {
      ultimo.pos = Math.min(ultimo.pos, grupo.pos)
      continue
    }
    linhasDoTexto.push({ ...grupo })
  }
  return linhasDoTexto.map((grupo, indice) => {
    const proxima = linhasDoTexto[indice + 1]
    const salto = proxima ? proxima.top - grupo.top : alturaLinha
    const altura = salto > alturaLinha * 1.75 ? alturaLinha : Math.max(salto, alturaLinha)
    return {
      pos: grupo.pos,
      altura: altura + (indice === linhasDoTexto.length - 1 ? margemBaixo : 0),
      forcarQuebra: false,
    }
  })
}

function coletarLinhas(view: EditorView): LinhaFolha[] {
  const linhas: LinhaFolha[] = []
  view.state.doc.descendants((node, pos) => {
    if (node.type.name === 'quebraDePagina') {
      linhas.push(...linhasDoBloco(view, node, pos))
      return false
    }
    if (node.isTextblock) {
      linhas.push(...linhasDoBloco(view, node, pos))
      return false
    }
    return true
  })
  return linhas
}

function intervalo(
  alturaRestante: number,
  margemSuperior: number,
  margemInferior: number,
  pagina: number,
): HTMLElement {
  const caixa = document.createElement('span')
  caixa.className = 'folha-intervalo'
  caixa.contentEditable = 'false'
  caixa.setAttribute('aria-hidden', 'true')

  const fim = document.createElement('span')
  fim.className = 'folha-fim'
  fim.style.height = `${Math.max(0, alturaRestante) + margemInferior}px`

  const vao = document.createElement('span')
  vao.className = 'folha-vao'
  vao.style.height = `${FOLHA_A4.vaoPx}px`

  const inicio = document.createElement('span')
  inicio.className = 'folha-inicio'
  inicio.dataset.folha = String(pagina)
  inicio.style.height = `${margemSuperior}px`

  caixa.append(fim, vao, inicio)
  return caixa
}

function sobraDaFolha(altura: number): HTMLElement {
  const caixa = document.createElement('span')
  caixa.className = 'folha-sobra'
  caixa.contentEditable = 'false'
  caixa.style.height = `${Math.max(0, altura)}px`
  caixa.setAttribute('aria-hidden', 'true')
  return caixa
}

export const PaginacaoMinuta = Extension.create({
  name: 'paginacao',

  addStorage() {
    return { paginas: 1 }
  },

  addProseMirrorPlugins() {
    const storage = this.storage
    let assinatura = ''
    let quadro = 0
    let tentativas = 0

    const recalcular = (view: EditorView) => {
      if (!view.dom.isConnected) {
        return
      }
      const largura = view.dom.getBoundingClientRect().width
      if (largura < 40) {
        return
      }
      const margemSuperior = margem(view.dom, 'top')
      const margemInferior = margem(view.dom, 'bottom')
      const alturaFolha = largura * (FOLHA_A4.alturaMm / FOLHA_A4.larguraMm)
      const alturaUtil = Math.max(1, alturaFolha - margemSuperior - margemInferior)
      const distribuicao = distribuirEmFolhas(coletarLinhas(view), alturaUtil)
      const proxima = distribuicao.quebras
        .map((quebra) => `${quebra.pos}:${Math.round(quebra.restante)}`)
        .join('.')
        .concat(`|${Math.round(distribuicao.sobra)}|${distribuicao.paginas}`)
      if (proxima === assinatura) {
        tentativas = 0
        return
      }
      tentativas += 1
      if (tentativas > 8) {
        return
      }
      assinatura = proxima
      storage.paginas = distribuicao.paginas

      const widgets = distribuicao.quebras.map((quebra, indice) =>
        Decoration.widget(
          quebra.pos,
          () => intervalo(quebra.restante, margemSuperior, margemInferior, indice + 2),
          {
            side: -1,
            ignoreSelection: true,
            key: `folha-${quebra.pos}-${Math.round(quebra.restante)}`,
          },
        ),
      )

      if (distribuicao.sobra > 1) {
        widgets.push(
          Decoration.widget(view.state.doc.content.size, () => sobraDaFolha(distribuicao.sobra), {
            side: 1,
            ignoreSelection: true,
            key: `folha-sobra-${Math.round(distribuicao.sobra)}`,
          }),
        )
      }

      const tr = view.state.tr.setMeta(chavePaginacao, {
        deco: DecorationSet.create(view.state.doc, widgets),
        paginas: distribuicao.paginas,
      })
      tr.setMeta('addToHistory', false)
      view.dispatch(tr)
    }

    const agendar = (view: EditorView) => {
      cancelAnimationFrame(quadro)
      quadro = requestAnimationFrame(() => recalcular(view))
    }

    return [
      new Plugin({
        key: chavePaginacao,
        state: {
          init: () => ({ deco: DecorationSet.empty, paginas: 1 }),
          apply(tr, valor) {
            const meta = tr.getMeta(chavePaginacao) as { deco: DecorationSet; paginas: number } | undefined
            if (meta) {
              return meta
            }
            return { deco: valor.deco.map(tr.mapping, tr.doc), paginas: valor.paginas }
          },
        },
        props: {
          decorations(state) {
            return chavePaginacao.getState(state)?.deco ?? DecorationSet.empty
          },
        },
        view(view) {
          let ativo = true
          const observar = new ResizeObserver(() => agendar(view))
          observar.observe(view.dom)
          agendar(view)
          void document.fonts?.ready.then(() => {
            if (!ativo) {
              return
            }
            tentativas = 0
            assinatura = ''
            agendar(view)
          })
          return {
            update: (atual, anterior) => {
              if (!anterior.doc.eq(atual.state.doc)) {
                tentativas = 0
                agendar(atual)
              }
            },
            destroy: () => {
              ativo = false
              cancelAnimationFrame(quadro)
              observar.disconnect()
            },
          }
        },
      }),
    ]
  },
})

export function totalDePaginas(editor: { storage: object } | null): number {
  const dados = (editor?.storage as { paginacao?: { paginas?: number } } | undefined)?.paginacao
  return dados?.paginas && dados.paginas > 0 ? dados.paginas : 1
}

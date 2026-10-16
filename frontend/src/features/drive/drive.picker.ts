import { MIMES_DO_SELETOR } from './drive.constants'
import type { PickerToken } from './drive.types'

/**
 * Seletor de arquivos do Google (ADR-022: exceção documentada).
 *
 * O script do Google só é carregado quando a pessoa clica em "Escolher do
 * Google Drive" — nunca junto com a página. O token curto recebido do backend
 * vive só nesta função: não vai para storage, store nem log.
 */

interface PickerDoc {
  id: string
}

interface PickerResposta {
  action: string
  docs?: PickerDoc[]
}

interface DocsViewFalso {
  setIncludeFolders(valor: boolean): DocsViewFalso
  setSelectFolderEnabled(valor: boolean): DocsViewFalso
  setMimeTypes(mimes: string): DocsViewFalso
}

interface PickerBuilderFalso {
  addView(view: DocsViewFalso): PickerBuilderFalso
  setOAuthToken(token: string): PickerBuilderFalso
  setDeveloperKey(chave: string): PickerBuilderFalso
  setAppId(id: string): PickerBuilderFalso
  setLocale(idioma: string): PickerBuilderFalso
  setTitle(titulo: string): PickerBuilderFalso
  enableFeature(feature: string): PickerBuilderFalso
  setCallback(fn: (resposta: PickerResposta) => void): PickerBuilderFalso
  build(): { setVisible(visivel: boolean): void }
}

interface GooglePicker {
  DocsView: new (viewId: string) => DocsViewFalso
  PickerBuilder: new () => PickerBuilderFalso
  ViewId: { DOCS: string }
  Feature: { MULTISELECT_ENABLED: string }
  Action: { PICKED: string; CANCEL: string }
}

interface Gapi {
  load(api: string, opcoes: { callback: () => void; onerror?: () => void }): void
}

declare global {
  interface Window {
    gapi?: Gapi
    google?: { picker?: GooglePicker }
  }
}

const URL_DO_SCRIPT = 'https://apis.google.com/js/api.js'

let carregamento: Promise<GooglePicker> | null = null

function carregarScript(): Promise<void> {
  return new Promise((resolver, rejeitar) => {
    if (window.gapi) {
      resolver()
      return
    }
    const script = document.createElement('script')
    script.src = URL_DO_SCRIPT
    script.async = true
    script.onload = () => resolver()
    script.onerror = () => rejeitar(new Error('script_do_google'))
    document.head.appendChild(script)
  })
}

function carregarPicker(): Promise<GooglePicker> {
  if (!carregamento) {
    carregamento = carregarScript()
      .then(
        () =>
          new Promise<GooglePicker>((resolver, rejeitar) => {
            const gapi = window.gapi
            if (!gapi) {
              rejeitar(new Error('script_do_google'))
              return
            }
            gapi.load('picker', {
              callback: () => {
                const picker = window.google?.picker
                if (picker) {
                  resolver(picker)
                } else {
                  rejeitar(new Error('script_do_google'))
                }
              },
              onerror: () => rejeitar(new Error('script_do_google')),
            })
          }),
      )
      .catch((erro: unknown) => {
        // Permite tentar de novo se a rede falhou.
        carregamento = null
        throw erro
      })
  }
  return carregamento
}

export const ERRO_SCRIPT_DO_GOOGLE = 'script_do_google'

/**
 * Abre o seletor e devolve os ids escolhidos (vazio se a pessoa cancelar).
 * Recebe uma função para buscar o token só depois do script carregar, para o
 * token curto não ficar esperando.
 */
export async function escolherArquivosDoGoogle(
  buscarToken: () => Promise<PickerToken>,
): Promise<string[]> {
  const picker = await carregarPicker()
  const credenciais = await buscarToken()

  return new Promise<string[]>((resolver) => {
    const visao = new picker.DocsView(picker.ViewId.DOCS)
      .setIncludeFolders(false)
      .setSelectFolderEnabled(false)
      .setMimeTypes(MIMES_DO_SELETOR.join(','))

    const janela = new picker.PickerBuilder()
      .addView(visao)
      .setOAuthToken(credenciais.access_token)
      .setDeveloperKey(credenciais.api_key)
      .setAppId(credenciais.app_id)
      .setLocale('pt-BR')
      .setTitle('Escolher arquivos do Google Drive')
      .enableFeature(picker.Feature.MULTISELECT_ENABLED)
      .setCallback((resposta) => {
        if (resposta.action === picker.Action.PICKED) {
          resolver((resposta.docs ?? []).map((doc) => doc.id))
        } else if (resposta.action === picker.Action.CANCEL) {
          resolver([])
        }
      })
      .build()
    janela.setVisible(true)
  })
}

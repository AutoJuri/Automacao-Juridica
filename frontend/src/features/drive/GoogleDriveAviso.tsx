import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Check, Cloud, Loader2, Unplug } from 'lucide-react'

import { MUITAS_TENTATIVAS, mensagemDeErro } from '#/features/auth/auth.errors'

import { PARAM_RESULTADO_GOOGLE, driveGoogleStatusKey } from './drive.constants'
import { useConectarGoogle, useDesconectarGoogle, useStatusGoogle } from './drive.queries'

type Resultado = 'conectado' | 'erro' | 'escopo'

const MENSAGEM_RESULTADO: Record<Resultado, { texto: string; ok: boolean }> = {
  conectado: { texto: 'Google Drive conectado.', ok: true },
  erro: {
    texto: 'Não foi possível conectar o Google Drive. Tente de novo.',
    ok: false,
  },
  escopo: {
    texto:
      'A permissão para criar e abrir arquivos no Drive não foi concedida. Conecte de novo e deixe essa opção marcada.',
    ok: false,
  },
}

function lerResultado(): Resultado | null {
  const valor = new URLSearchParams(window.location.search).get(PARAM_RESULTADO_GOOGLE)
  return valor === 'conectado' || valor === 'erro' || valor === 'escopo' ? valor : null
}

/** Tira `?google=` da barra de endereço sem recarregar nem criar histórico. */
function limparResultadoDaUrl() {
  const url = new URL(window.location.href)
  url.searchParams.delete(PARAM_RESULTADO_GOOGLE)
  window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash)
}

interface GoogleDriveAvisoProps {
  /** Dentro de uma pasta: some quando já está conectado. */
  compacto?: boolean
}

/** Cartão de conexão com o Google Drive. Só mostra estado; quem protege é o backend. */
export function GoogleDriveAviso({ compacto = false }: GoogleDriveAvisoProps) {
  const cliente = useQueryClient()
  const status = useStatusGoogle()
  const conectar = useConectarGoogle()
  const desconectar = useDesconectarGoogle()
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [confirmar, setConfirmar] = useState(false)

  useEffect(() => {
    const lido = lerResultado()
    if (!lido) {
      return
    }
    setResultado(lido)
    limparResultadoDaUrl()
    void cliente.invalidateQueries({ queryKey: driveGoogleStatusKey() })
  }, [cliente])

  const erroAcao = conectar.error
    ? mensagemDeErro(conectar.error, {
        429: MUITAS_TENTATIVAS,
        503: 'A conexão com o Google Drive ainda não foi configurada neste servidor.',
      })
    : desconectar.error
      ? mensagemDeErro(desconectar.error, {
          401: 'Sessão expirada. Entre novamente.',
        })
      : null

  if (status.isLoading || status.isError || !status.data) {
    return null
  }

  const { configurado, conectado } = status.data
  const aviso = resultado ? MENSAGEM_RESULTADO[resultado] : null

  if (conectado && compacto && !aviso && !erroAcao) {
    return null
  }

  return (
    <div className="mb-6 space-y-2">
      {aviso ? (
        <p
          role="status"
          className={[
            'rounded-lg border px-3 py-2 text-[13px]',
            aviso.ok
              ? 'border-[#BBF7D0] bg-[#F0FDF4] text-[#166534]'
              : 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]',
          ].join(' ')}
        >
          {aviso.texto}
        </p>
      ) : null}

      <div className="flex flex-col gap-3 rounded-xl border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          {conectado ? (
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#16A34A]" aria-hidden />
          ) : (
            <Cloud className="mt-0.5 h-4 w-4 shrink-0 text-[#6B7280]" aria-hidden />
          )}
          <p className="text-[13px] text-[#4B5563]">
            {conectado
              ? 'Google Drive conectado. Os arquivos ficam na sua conta, em uma pasta “AdvogAtiva”.'
              : configurado
                ? 'Conecte o Google Drive para guardar os arquivos das pastas na sua própria conta. O acesso é só aos arquivos que a plataforma criar ou que você escolher.'
                : 'A conexão com o Google Drive ainda não foi configurada neste servidor. As pastas já funcionam normalmente.'}
          </p>
        </div>

        {conectado ? (
          <button
            type="button"
            disabled={desconectar.isPending}
            onBlur={() => setConfirmar(false)}
            onClick={() => {
              if (!confirmar) {
                setConfirmar(true)
                return
              }
              setConfirmar(false)
              desconectar.mutate()
            }}
            className={[
              'inline-flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg border px-3 text-[12px] font-semibold transition-colors',
              confirmar
                ? 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] hover:bg-[#FEE2E2]'
                : 'border-[#E5E7EB] bg-white text-[#374151] hover:border-[#FECACA] hover:bg-[#FEF2F2] hover:text-[#B91C1C]',
            ].join(' ')}
          >
            {desconectar.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : (
              <Unplug className="h-3.5 w-3.5" aria-hidden />
            )}
            {confirmar ? 'Desconectar?' : 'Desconectar'}
          </button>
        ) : configurado ? (
          <button
            type="button"
            disabled={conectar.isPending}
            onClick={() => conectar.mutate()}
            className="inline-flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] active:bg-[#1E40AF] disabled:opacity-70"
          >
            {conectar.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : null}
            Conectar Google Drive
          </button>
        ) : null}
      </div>

      {conectado && confirmar ? (
        <p className="text-[12px] text-[#6B7280]">
          Os arquivos continuam no seu Google Drive e as pastas continuam aqui. Só o acesso da
          plataforma é removido.
        </p>
      ) : null}
      {erroAcao ? <p className="text-[13px] text-[#B91C1C]">{erroAcao}</p> : null}
    </div>
  )
}

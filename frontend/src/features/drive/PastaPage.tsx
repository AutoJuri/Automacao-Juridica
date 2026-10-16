import { useState } from 'react'
import { isAxiosError } from 'axios'
import { useNavigate } from '@tanstack/react-router'
import { ArrowLeft, FileText, Folder, Pencil, Trash2 } from 'lucide-react'

import { mensagemDeErro } from '#/features/auth/auth.errors'
import { formatarNumeroCnj } from '#/features/processos/processos.format'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

import { ArquivosPasta } from './ArquivosPasta'
import { GoogleDriveAviso } from './GoogleDriveAviso'
import { PastaDialog } from './PastaDialog'
import { useExcluirPasta, usePasta } from './drive.queries'

interface PastaPageProps {
  pastaId: string
}

export function PastaPage({ pastaId }: PastaPageProps) {
  const navigate = useNavigate()
  const pasta = usePasta(pastaId)
  const excluir = useExcluirPasta()
  const [editando, setEditando] = useState(false)
  const [confirmar, setConfirmar] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  function voltar() {
    void navigate({ to: '/drive' })
  }

  async function excluirPasta() {
    setErro(null)
    try {
      await excluir.mutateAsync(pastaId)
      voltar()
    } catch (falha) {
      setErro(
        mensagemDeErro(falha, {
          401: 'Sessão expirada. Entre novamente.',
          404: 'Essa pasta não existe mais.',
        }),
      )
    }
  }

  if (pasta.isLoading) {
    return (
      <SecaoShell>
        <EstadoCarregando mensagem="Carregando pasta…" />
      </SecaoShell>
    )
  }

  if (pasta.isError || !pasta.data) {
    const naoExiste = isAxiosError(pasta.error) && pasta.error.response?.status === 404
    return (
      <SecaoShell>
        <button
          type="button"
          onClick={voltar}
          className="mb-4 inline-flex w-fit items-center gap-1.5 text-[13px] font-medium text-[#2563EB] transition-colors hover:text-[#1D4ED8]"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Voltar ao Drive
        </button>
        <p className="text-sm text-[#6B7280]">
          {naoExiste
            ? 'Pasta não encontrada.'
            : mensagemDeErro(pasta.error, {
                401: 'Sessão expirada. Entre novamente.',
              })}
        </p>
      </SecaoShell>
    )
  }

  const dados = pasta.data
  const processo = dados.processo
  const polos = processo ? [processo.autor, processo.reu].filter(Boolean).join(' × ') : ''

  return (
    <SecaoShell>
      <button
        type="button"
        onClick={voltar}
        className="mb-4 inline-flex w-fit items-center gap-1.5 text-[13px] font-medium text-[#2563EB] transition-colors hover:text-[#1D4ED8]"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Voltar ao Drive
      </button>

      <section className="mb-6 rounded-2xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB]">
              <Folder className="h-5 w-5" aria-hidden />
            </span>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold tracking-[0.18em] text-[#2563EB] uppercase">
                Pasta
              </p>
              <h1 className="truncate text-xl font-semibold text-[#111827]">{dados.nome}</h1>
              <p className="mt-1 flex items-center gap-1.5 text-sm text-[#6B7280]">
                <FileText className="h-3.5 w-3.5 shrink-0" aria-hidden />
                <span className="truncate">
                  {processo ? formatarNumeroCnj(processo.nu_processo) : 'Sem processo vinculado'}
                </span>
              </p>
              {polos ? <p className="mt-1 truncate text-[13px] text-[#374151]">{polos}</p> : null}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setEditando(true)}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-semibold text-[#374151] transition-colors hover:border-[#93C5FD] hover:bg-[#EFF6FF] hover:text-[#2563EB]"
            >
              <Pencil className="h-3.5 w-3.5" aria-hidden />
              Editar
            </button>
            <button
              type="button"
              disabled={excluir.isPending}
              onBlur={() => setConfirmar(false)}
              onClick={() => {
                if (!confirmar) {
                  setConfirmar(true)
                  return
                }
                void excluirPasta()
              }}
              className={[
                'inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-[12px] font-semibold transition-colors',
                confirmar
                  ? 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] hover:bg-[#FEE2E2]'
                  : 'border-[#E5E7EB] bg-white text-[#374151] hover:border-[#FECACA] hover:bg-[#FEF2F2] hover:text-[#B91C1C]',
              ].join(' ')}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
              {confirmar ? 'Excluir pasta?' : 'Excluir'}
            </button>
          </div>
        </div>
        {confirmar ? (
          <p className="mt-3 text-[12px] text-[#6B7280]">
            Excluir a pasta remove só a ficha daqui. Os arquivos continuam no seu Google Drive.
          </p>
        ) : null}
        {erro ? <p className="mt-3 text-[13px] text-[#B91C1C]">{erro}</p> : null}
      </section>

      <GoogleDriveAviso compacto />

      <ArquivosPasta pastaId={pastaId} />

      <PastaDialog aberto={editando} pasta={dados} onAberto={setEditando} />
    </SecaoShell>
  )
}

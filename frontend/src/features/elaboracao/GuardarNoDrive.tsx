import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { Check, Cloud, Loader2 } from 'lucide-react'

import { mensagemDoDrive } from '#/features/drive/drive.errors'
import { problemaDoArquivo } from '#/features/drive/drive.format'
import { useEnviarArquivo, usePastas, useStatusGoogle } from '#/features/drive/drive.queries'

interface GuardarNoDriveProps {
  arquivo: File
  /** Processo da elaboração: se há pasta ligada a ele, ela vem escolhida. */
  processoId: string | null
}

/**
 * Único ponto em que o anexo da peça modelo sai do navegador, e só por clique.
 * O envio vai para o backend, que valida e guarda no Google Drive da pessoa.
 */
export function GuardarNoDrive({ arquivo, processoId }: GuardarNoDriveProps) {
  const status = useStatusGoogle()
  const pastas = usePastas()
  const enviar = useEnviarArquivo()
  const [escolhida, setEscolhida] = useState<string | null>(null)
  const [guardadoEm, setGuardadoEm] = useState<{
    id: string
    nome: string
  } | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  if (status.isLoading || !status.data) {
    return null
  }

  const itens = pastas.data ?? []
  const padrao = processoId
    ? (itens.find((pasta) => pasta.processo?.id === processoId)?.id ?? '')
    : ''
  const pastaId = escolhida ?? padrao

  if (!status.data.conectado) {
    return (
      <p className="mt-2 text-[11px] text-[#6B7280]">
        Quer guardar este arquivo?{' '}
        <Link to="/drive" className="font-medium text-[#2563EB] hover:underline">
          Conecte o Google Drive
        </Link>
        .
      </p>
    )
  }

  if (itens.length === 0) {
    return (
      <p className="mt-2 text-[11px] text-[#6B7280]">
        Para guardar no Drive, crie antes uma pasta em{' '}
        <Link to="/drive" className="font-medium text-[#2563EB] hover:underline">
          Drive
        </Link>
        .
      </p>
    )
  }

  async function guardar() {
    setErro(null)
    setGuardadoEm(null)
    const pasta = itens.find((item) => item.id === pastaId)
    if (!pasta) {
      setErro('Escolha uma pasta.')
      return
    }
    const recusa = problemaDoArquivo(arquivo)
    if (recusa) {
      setErro(recusa)
      return
    }
    try {
      await enviar.mutateAsync({
        pastaId: pasta.id,
        arquivo,
        origem: 'elaboracao',
      })
      setGuardadoEm({ id: pasta.id, nome: pasta.nome })
    } catch (falha) {
      setErro(mensagemDoDrive(falha))
    }
  }

  return (
    <div className="mt-2 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-3 py-2">
      <div className="flex items-center gap-2">
        <select
          aria-label="Pasta do Drive"
          value={pastaId}
          disabled={enviar.isPending}
          onChange={(evento) => {
            setEscolhida(evento.target.value)
            setGuardadoEm(null)
          }}
          className="h-8 min-w-0 flex-1 rounded-md border border-[#E5E7EB] bg-white px-2 text-[12px] text-[#374151] outline-none focus:border-[#2563EB]"
        >
          <option value="">Escolher pasta…</option>
          {itens.map((pasta) => (
            <option key={pasta.id} value={pasta.id}>
              {pasta.nome}
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={enviar.isPending || !pastaId}
          onClick={() => {
            void guardar()
          }}
          className="inline-flex h-8 shrink-0 items-center gap-1 rounded-md bg-[#2563EB] px-2.5 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] disabled:opacity-50"
        >
          {enviar.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <Cloud className="h-3.5 w-3.5" aria-hidden />
          )}
          Guardar no Drive
        </button>
      </div>
      {guardadoEm ? (
        <p role="status" className="mt-2 flex items-center gap-1 text-[12px] text-[#166534]">
          <Check className="h-3.5 w-3.5" aria-hidden />
          Guardado em{' '}
          <Link
            to="/drive/$pastaId"
            params={{ pastaId: guardadoEm.id }}
            className="font-medium underline"
          >
            {guardadoEm.nome}
          </Link>
          .
        </p>
      ) : null}
      {erro ? (
        <p role="alert" className="mt-2 text-[12px] text-[#B91C1C]">
          {erro}
        </p>
      ) : null}
    </div>
  )
}

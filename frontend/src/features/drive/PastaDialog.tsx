import { useEffect, useState } from 'react'

import { Button } from '#/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '#/components/ui/dialog'
import { mensagemDeErro } from '#/features/auth/auth.errors'

import { NOME_PASTA_MAX } from './drive.constants'
import { useAtualizarPasta, useCriarPasta } from './drive.queries'
import type { AtualizarPasta, Pasta, PastaProcesso } from './drive.types'
import { SeletorProcesso } from './SeletorProcesso'

interface PastaDialogProps {
  aberto: boolean
  /** Pasta em edição. Nulo cria uma pasta nova. */
  pasta: Pasta | null
  onAberto: (aberto: boolean) => void
  onSalva?: (pasta: Pasta) => void
}

const ERROS = {
  401: 'Sessão expirada. Entre novamente.',
  404: 'Pasta ou processo não encontrado.',
  422: 'Confira o nome da pasta.',
}

export function PastaDialog({ aberto, pasta, onAberto, onSalva }: PastaDialogProps) {
  const criar = useCriarPasta()
  const atualizar = useAtualizarPasta()
  const [nome, setNome] = useState('')
  const [processo, setProcesso] = useState<PastaProcesso | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (aberto) {
      setNome(pasta?.nome ?? '')
      setProcesso(pasta?.processo ?? null)
      setErro(null)
    }
  }, [aberto, pasta])

  const nomeLimpo = nome.trim()
  const salvando = criar.isPending || atualizar.isPending

  async function salvar() {
    if (!nomeLimpo) {
      setErro('Informe o nome da pasta.')
      return
    }
    setErro(null)
    try {
      let salva: Pasta
      if (pasta) {
        const corpo: AtualizarPasta = {}
        if (nomeLimpo !== pasta.nome) {
          corpo.nome = nomeLimpo
        }
        if ((processo?.id ?? null) !== (pasta.processo?.id ?? null)) {
          corpo.processo_id = processo?.id ?? null
        }
        if (Object.keys(corpo).length === 0) {
          onAberto(false)
          return
        }
        salva = await atualizar.mutateAsync({ id: pasta.id, corpo })
      } else {
        salva = await criar.mutateAsync({
          nome: nomeLimpo,
          processoId: processo?.id ?? null,
        })
      }
      onAberto(false)
      onSalva?.(salva)
    } catch (falha) {
      setErro(mensagemDeErro(falha, ERROS))
    }
  }

  return (
    <Dialog open={aberto} onOpenChange={onAberto}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{pasta ? 'Editar pasta' : 'Nova pasta'}</DialogTitle>
          <DialogDescription>
            Dê um nome à pasta. Ligar a um processo é opcional e pode mudar depois.
          </DialogDescription>
        </DialogHeader>

        <form
          className="min-w-0 space-y-4"
          onSubmit={(event) => {
            event.preventDefault()
            void salvar()
          }}
        >
          <div>
            <label
              htmlFor="drive-pasta-nome"
              className="mb-1.5 block text-[12px] font-semibold text-[#374151]"
            >
              Nome da pasta
            </label>
            <input
              id="drive-pasta-nome"
              autoFocus
              value={nome}
              maxLength={NOME_PASTA_MAX}
              placeholder="Ex.: Contratos do cliente"
              onChange={(event) => setNome(event.target.value)}
              className="h-9 w-full rounded-lg border border-[#E5E7EB] bg-white px-3 text-[13px] text-[#111827] transition-colors outline-none placeholder:text-[#9CA3AF] hover:border-[#BFDBFE] focus:border-[#2563EB] focus:ring-2 focus:ring-[#DBEAFE]"
            />
          </div>

          <div>
            <p className="mb-1.5 text-[12px] font-semibold text-[#374151]">
              Processo <span className="font-normal text-[#9CA3AF]">(opcional)</span>
            </p>
            <SeletorProcesso selecionado={processo} onChange={setProcesso} />
          </div>

          {erro ? <p className="text-[13px] text-[#B91C1C]">{erro}</p> : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onAberto(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              className="bg-[#2563EB] text-white hover:bg-[#1D4ED8]"
              disabled={salvando || !nomeLimpo}
            >
              {salvando ? 'Salvando…' : pasta ? 'Salvar' : 'Criar pasta'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

import { useState } from 'react'

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

import { modelosPeca } from './elaboracao.mock'
import { SeletorPeca } from './SeletorPeca'
import { useCriarElaboracao } from './elaboracoes.queries'

interface IniciarElaboracaoDialogProps {
  aberto: boolean
  processoId: string | null
  onAberto: (aberto: boolean) => void
  onCriada: (elaboracaoId: string) => void
}

export function IniciarElaboracaoDialog({
  aberto,
  processoId,
  onAberto,
  onCriada,
}: IniciarElaboracaoDialogProps) {
  const criar = useCriarElaboracao()
  const [peca, setPeca] = useState(modelosPeca[0].id)
  const [erro, setErro] = useState<string | null>(null)

  async function confirmar() {
    if (!processoId) {
      return
    }
    setErro(null)
    try {
      const detalhe = await criar.mutateAsync({ processoId, peca })
      onCriada(detalhe.id)
    } catch (falha) {
      setErro(
        mensagemDeErro(falha, {
          401: 'Sessão expirada. Entre novamente.',
          404: 'Processo não encontrado.',
        }),
      )
    }
  }

  return (
    <Dialog
      open={aberto}
      onOpenChange={(proximo) => {
        if (!proximo) {
          setErro(null)
          setPeca(modelosPeca[0].id)
        }
        onAberto(proximo)
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Iniciar elaboração</DialogTitle>
          <DialogDescription>
            Escolha a peça. Se ela já existir neste processo, a elaboração é reaberta.
          </DialogDescription>
        </DialogHeader>
        <SeletorPeca pecaSelecionada={peca} onChange={setPeca} mostrarSugestao={false} />
        {erro ? <p className="text-[13px] text-[#B91C1C]">{erro}</p> : null}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onAberto(false)}>
            Cancelar
          </Button>
          <Button
            type="button"
            className="bg-[#2563EB] text-white"
            disabled={criar.isPending || !processoId}
            onClick={() => {
              void confirmar()
            }}
          >
            {criar.isPending ? 'Abrindo…' : 'Continuar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

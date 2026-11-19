import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

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

import { obterOuCriarElaboracao } from './elaboracao.api'
import type { ElaboracaoSessao } from './elaboracao.types'
import { modelosPeca } from './elaboracao.mock'
import { SeletorPeca } from './SeletorPeca'
import { ELABORACOES_QUERY_KEY } from './elaboracoes.constants'

interface IniciarElaboracaoDialogProps {
  aberto: boolean
  processoId: string | null
  onAberto: (aberto: boolean) => void
  aoCriar?: (sessao: ElaboracaoSessao) => Promise<void>
  onCriada: (elaboracaoId: string) => void
}

export function IniciarElaboracaoDialog({
  aberto,
  processoId,
  onAberto,
  aoCriar,
  onCriada,
}: IniciarElaboracaoDialogProps) {
  const queryClient = useQueryClient()
  const [peca, setPeca] = useState(modelosPeca[0].id)
  const [erro, setErro] = useState<string | null>(null)
  const [pendente, setPendente] = useState(false)

  async function confirmar() {
    if (!processoId) {
      return
    }
    setErro(null)
    setPendente(true)
    try {
      const sessao = await obterOuCriarElaboracao(processoId, peca)
      await queryClient.invalidateQueries({ queryKey: ELABORACOES_QUERY_KEY })
      if (aoCriar) {
        await aoCriar(sessao)
      }
      onCriada(sessao.id)
    } catch (falha) {
      setErro(
        mensagemDeErro(falha, {
          401: 'Sessão expirada. Entre novamente.',
          404: 'Processo não encontrado.',
        }),
      )
    } finally {
      setPendente(false)
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
            disabled={pendente || !processoId}
            onClick={() => {
              void confirmar()
            }}
          >
            {pendente ? 'Abrindo…' : 'Continuar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

import type { TomDaColuna } from './tarefas.board'

/** Fundos claros e títulos escuros o bastante para ler. O card continua branco em cima. */
export const CORES_COLUNA: Record<
  TomDaColuna,
  {
    fundo: string
    borda: string
    texto: string
    ponto: string
    badge: string
    faixa: string
    botao: string
  }
> = {
  fazer: {
    fundo: 'bg-[#EEF4FF]',
    borda: 'border-[#C7DBFC]',
    texto: 'text-[#1D4ED8]',
    ponto: 'bg-[#2563EB]',
    badge: 'bg-[#DBEAFE] text-[#1D4ED8]',
    faixa: 'bg-[#2563EB]',
    botao: 'text-[#1D4ED8] hover:bg-[#EEF4FF]',
  },
  andamento: {
    fundo: 'bg-[#FFF8EB]',
    borda: 'border-[#F6E0B5]',
    texto: 'text-[#B45309]',
    ponto: 'bg-[#F59E0B]',
    badge: 'bg-[#FEF3C7] text-[#B45309]',
    faixa: 'bg-[#F59E0B]',
    botao: 'text-[#B45309] hover:bg-[#FFF8EB]',
  },
  conclusao: {
    fundo: 'bg-[#F0FDF4]',
    borda: 'border-[#BBF7D0]',
    texto: 'text-[#15803D]',
    ponto: 'bg-[#16A34A]',
    badge: 'bg-[#DCFCE7] text-[#15803D]',
    faixa: 'bg-[#16A34A]',
    botao: 'text-[#15803D] hover:bg-[#F0FDF4]',
  },
}

import { ExternalLink } from 'lucide-react'
import { ScrollArea } from '#/components/ui/scroll-area'
import { textoContestacaoMock } from './elaboracao.mock'

interface DocumentViewerProps {
  editando: boolean
  highlightAtivo: boolean
  pecaNome: string
}

export function DocumentViewer({ editando, highlightAtivo, pecaNome }: DocumentViewerProps) {
  // Divide o texto em parágrafos para renderizar com formatação
  const paragrafos = textoContestacaoMock.split('\n\n')

  return (
    <ScrollArea className="flex-1 min-h-0">
      <div
        className={`mx-auto max-w-[780px] my-6 rounded-lg shadow-sm border transition-all duration-200 ${
          editando
            ? 'border-[#3B5BDB] ring-2 ring-[#3B5BDB]/20'
            : 'border-[#E5E7EB]'
        } bg-white`}
      >
        {/* Barra de status do documento */}
        <div className="flex items-center justify-between px-8 py-3 border-b border-[#F3F4F6]">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-widest uppercase">
              {pecaNome}
            </span>
            {editando && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-semibold bg-[#EEF2FF] text-[#3B5BDB] border border-[#3B5BDB]/20">
                Modo edição
              </span>
            )}
          </div>
          <span className="text-[10px] text-[#9CA3AF]">Versão 3 — 01:12</span>
        </div>

        {/* Corpo do documento */}
        <div
          className={`px-10 py-8 ${editando ? 'cursor-text' : 'cursor-default'} select-text`}
        >
          {paragrafos.map((paragrafo, index) => {
            const isTitulo = paragrafo.length < 100 && paragrafo === paragrafo.toUpperCase() && paragrafo.trim() !== ''
            const isSubtitulo = /^[IVX]+\s—/.test(paragrafo.trim())
            const temCitacao1 = paragrafo.includes('Superior Tribunal de Justiça ¹')
            const temCitacao2 = paragrafo.includes('TJSP ²')

            if (!paragrafo.trim()) return null

            if (isTitulo && index === 0) {
              return (
                <p key={index} className="text-[13px] font-semibold text-[#111827] text-center uppercase mb-6 leading-snug">
                  {paragrafo}
                </p>
              )
            }

            if (paragrafo.startsWith('Processo nº') || paragrafo.startsWith('ACME INDUSTRIAL')) {
              return (
                <p key={index} className="text-[13px] text-[#374151] mb-3 leading-relaxed">
                  {paragrafo}
                </p>
              )
            }

            if (paragrafo === 'CONTESTAÇÃO') {
              return (
                <p key={index} className="text-[15px] font-bold text-[#111827] text-center uppercase my-6 tracking-wide">
                  {paragrafo}
                </p>
              )
            }

            if (isSubtitulo) {
              return (
                <p key={index} className="text-[13px] font-bold text-[#111827] uppercase mb-3 mt-5 tracking-wide">
                  {paragrafo}
                </p>
              )
            }

            if (paragrafo.startsWith('3.1.') || paragrafo.startsWith('3.2.')) {
              return (
                <p key={index} className="text-[13px] font-semibold text-[#111827] uppercase mb-2 mt-4">
                  {paragrafo}
                </p>
              )
            }

            if (paragrafo.includes('[continua...]')) {
              return (
                <p key={index} className="text-[13px] text-[#9CA3AF] italic mt-4">
                  {paragrafo}
                </p>
              )
            }

            // Parágrafos com citações de jurisprudência
            if (temCitacao1 || temCitacao2) {
              const partes = paragrafo.split(temCitacao1 ? 'Superior Tribunal de Justiça ¹' : 'TJSP ²')
              const marcador = temCitacao1 ? 'Superior Tribunal de Justiça' : 'TJSP'
              const nota = temCitacao1 ? '¹' : '²'
              return (
                <p key={index} className="text-[13px] text-[#374151] mb-3 leading-relaxed text-justify">
                  {partes[0]}
                  <span
                    className={`inline-flex items-baseline gap-0.5 font-semibold ${
                      highlightAtivo ? 'bg-[#FEF9C3] text-[#92400E] px-0.5 rounded' : 'text-[#111827]'
                    }`}
                  >
                    {marcador}
                    {highlightAtivo && (
                      <ExternalLink className="w-3 h-3 text-[#3B5BDB] inline ml-0.5 cursor-pointer" />
                    )}
                    <sup className="text-[#3B5BDB] ml-0.5 text-[10px]">{nota}</sup>
                  </span>
                  {partes[1]}
                </p>
              )
            }

            return (
              <p key={index} className="text-[13px] text-[#374151] mb-3 leading-relaxed text-justify">
                {paragrafo}
              </p>
            )
          })}

          {/* Popup mock de jurisprudência highlight */}
          {highlightAtivo && (
            <div className="mt-6 mx-auto max-w-lg border border-[#E5E7EB] rounded-xl bg-[#FAFAFA] p-4 shadow-sm">
              <div className="flex items-start gap-2 mb-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#3B5BDB] mt-1.5 shrink-0" />
                <div>
                  <p className="text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-widest mb-0.5">
                    Jurisprudência selecionada
                  </p>
                  <p className="text-[12px] font-semibold text-[#111827]">
                    STJ — REsp 1.234.567/SP
                  </p>
                </div>
              </div>
              <p className="text-[11px] text-[#6B7280] leading-snug mb-3">
                "A manutenção indevida de restrição após quitação configura ato ilícito nos termos do art. 927 do CC, gerando responsabilidade civil objetiva da instituição."
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value="Como usar esta jurisprudência na peça..."
                  className="flex-1 border border-[#E5E7EB] rounded-md px-2.5 py-1.5 text-[11px] text-[#9CA3AF] bg-white cursor-default"
                />
                <button className="px-3 py-1.5 rounded-md bg-[#3B5BDB] text-white text-[11px] font-semibold cursor-default">
                  Executar
                </button>
              </div>
            </div>
          )}

          {/* Notas de rodapé */}
          <div className="mt-8 pt-4 border-t border-[#E5E7EB]">
            <p className="text-[10px] text-[#9CA3AF] mb-1">
              <sup>¹</sup> STJ — AgInt no REsp 1.938.417/SP, 3ª Turma, Rel. Min. Ricardo Villas Bôas Cueva, j. 14/03/2023.
            </p>
            <p className="text-[10px] text-[#9CA3AF]">
              <sup>²</sup> TJSP — AC 1011234-99.2025.8.26.0100, 30ª Câmara de Direito Privado, Rel. Des. Lino Machado, j. 02/04/2026.
            </p>
          </div>
        </div>
      </div>
    </ScrollArea>
  )
}

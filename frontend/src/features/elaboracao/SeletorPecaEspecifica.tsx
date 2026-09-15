import { useRef, useState } from 'react'
import { FileText, UploadCloud, X } from 'lucide-react'
import { extensaoArquivo, FOCO_CAMPO, propsFocoCampo, validarArquivoModelo } from './elaboracao.ui'

interface ArquivoModelo {
  nome: string
  tamanho: number
}

export function SeletorPecaEspecifica() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [arquivo, setArquivo] = useState<ArquivoModelo | null>(null)
  const [texto, setTexto] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [arrastando, setArrastando] = useState(false)

  function aplicarArquivo(file: File) {
    const recusa = validarArquivoModelo(file)
    if (recusa) {
      setErro(recusa)
      return
    }
    setErro(null)
    setArquivo({ nome: file.name, tamanho: file.size })
    const ext = extensaoArquivo(file.name)
    if (ext === 'txt') {
      const leitor = new FileReader()
      leitor.onload = () => {
        const lido = typeof leitor.result === 'string' ? leitor.result : ''
        setTexto(lido)
      }
      leitor.readAsText(file)
      return
    }
  }

  return (
    <div>
      <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Peça modelo específica
      </p>
      <p className="text-[12px] text-[#6B7280] leading-snug mb-3">
        O arquivo e o texto ficam só neste browser, para você consultar o estilo.
        Nada é enviado ao servidor — a IA ainda não assimila o modelo.
      </p>

      <input
        ref={inputRef}
        type="file"
        accept=".txt,.pdf,.docx,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) {
            aplicarArquivo(file)
          }
          e.target.value = ''
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setArrastando(true)
        }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => {
          e.preventDefault()
          setArrastando(false)
          const file = e.dataTransfer.files[0]
          if (file) {
            aplicarArquivo(file)
          }
        }}
        className={[
          'w-full border-2 border-dashed rounded-xl p-5 flex flex-col items-center gap-1.5 cursor-pointer transition-colors',
          arrastando
            ? 'border-[#2563EB] bg-[#DBEAFE]'
            : 'border-[#D1D5DB] bg-[#F8F9FC] hover:border-[#2563EB] hover:bg-[#EFF6FF]',
        ].join(' ')}
      >
        <UploadCloud className="w-8 h-8 text-[#2563EB]" aria-hidden />
        <p className="text-[12px] font-medium text-[#374151] text-center">
          Arraste ou clique para enviar TXT, PDF, DOCX
        </p>
        <p className="text-[11px] text-[#9CA3AF]">Máximo 5 MB · não sai deste computador</p>
      </button>

      {arquivo ? (
        <div className="mt-2 flex items-start gap-2 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2">
          <FileText className="w-4 h-4 text-[#2563EB] mt-0.5 shrink-0" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-medium text-[#111827] truncate">{arquivo.nome}</p>
            <p className="text-[11px] text-[#6B7280]">
              {(arquivo.tamanho / 1024).toFixed(1)} KB
              {extensaoArquivo(arquivo.nome) !== 'txt'
                ? ' · PDF/DOCX anexado (o texto não é extraído daqui)'
                : ' · texto copiado para o campo abaixo'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setArquivo(null)
              setErro(null)
            }}
            className="h-7 w-7 inline-flex items-center justify-center rounded-md text-[#6B7280] hover:bg-[#F3F4F6]"
            aria-label="Remover arquivo"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : null}

      {erro ? <p className="mt-2 text-[12px] text-[#B45309]">{erro}</p> : null}

      <textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        rows={4}
        placeholder="Ou cole aqui o texto da tese/modelo..."
        className={`mt-3 w-full resize-none rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      />
    </div>
  )
}

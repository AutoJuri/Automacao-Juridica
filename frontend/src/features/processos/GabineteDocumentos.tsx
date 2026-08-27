import { ExternalLink } from 'lucide-react'
import { urlEsajHttps } from './processos.urls'

interface GabineteDocumentosProps {
  urlCpo: string | null
  urlPasta: string | null
}

export function GabineteDocumentos({ urlCpo, urlPasta }: GabineteDocumentosProps) {
  const hrefCpo = urlEsajHttps(urlCpo)
  const hrefPasta = urlEsajHttps(urlPasta)

  return (
    <div className="flex flex-col">
      <div className="mb-4">
        <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
          Gabinete de Documentos
        </p>
        <p className="text-[11px] text-[#9CA3AF] mt-1">
          PDFs do processo ainda não são coletados
        </p>
      </div>

      <div className="flex-1 rounded-xl border border-dashed border-[#E5E7EB] bg-[#FAFAFA] flex flex-col items-center justify-center px-6 text-center min-h-[200px] gap-3">
        <p className="text-[13px] text-[#6B7280] leading-relaxed">
          Documentos ainda não coletados.
        </p>
        <div className="flex flex-col gap-2">
          {hrefCpo ? (
            <a
              href={hrefCpo}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 text-[12px] font-medium text-[#3B5BDB] hover:underline"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Abrir no e-SAJ (CPO)
            </a>
          ) : null}
          {hrefPasta ? (
            <a
              href={hrefPasta}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 text-[12px] font-medium text-[#3B5BDB] hover:underline"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Pasta digital
            </a>
          ) : null}
        </div>
      </div>
    </div>
  )
}

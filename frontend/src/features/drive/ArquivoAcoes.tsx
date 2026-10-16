import { useState } from 'react';
import { Download, ExternalLink, Loader2, Trash2 } from 'lucide-react';

import type { ArquivoDrive, Pasta } from './drive.types';

interface ArquivoAcoesProps {
  arquivo: ArquivoDrive;
  destinos: Pasta[];
  ocupado: boolean;
  baixando: boolean;
  /** Na grade os botões ficam só com ícone, para caber no cartão. */
  compacto?: boolean;
  onBaixar: (arquivo: ArquivoDrive) => void;
  onMover: (arquivo: ArquivoDrive, pastaId: string) => void;
  onExcluir: (arquivo: ArquivoDrive) => void;
}

const BOTAO =
  'inline-flex h-8 items-center justify-center gap-1 rounded-md px-2 text-[12px] font-medium text-[#4B5563] transition-colors hover:bg-[#EFF6FF] hover:text-[#2563EB] disabled:opacity-50';

export function ArquivoAcoes({
  arquivo,
  destinos,
  ocupado,
  baixando,
  compacto = false,
  onBaixar,
  onMover,
  onExcluir,
}: ArquivoAcoesProps) {
  const [confirmar, setConfirmar] = useState(false);
  const escolhidoNoDrive = arquivo.origem === 'drive';
  const rotuloTirar = escolhidoNoDrive ? 'Tirar' : 'Excluir';
  const rotuloConfirma = escolhidoNoDrive ? 'Tirar?' : 'Excluir?';

  return (
    <div
      className={
        compacto
          ? 'flex flex-wrap items-center gap-1'
          : 'flex shrink-0 flex-wrap items-center gap-1'
      }
    >
      <button
        type="button"
        className={BOTAO}
        disabled={ocupado || baixando || arquivo.ausente_no_google}
        onClick={() => onBaixar(arquivo)}
        aria-label={`Baixar ${arquivo.nome}`}
        title="Baixar"
      >
        {baixando ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
        ) : (
          <Download className="h-3.5 w-3.5" aria-hidden />
        )}
        {compacto ? null : 'Baixar'}
      </button>

      {arquivo.ausente_no_google ? null : (
        <a
          href={arquivo.url_drive}
          target="_blank"
          rel="noopener noreferrer"
          className={BOTAO}
          aria-label={`Abrir ${arquivo.nome} no Google Drive`}
          title="Abrir no Drive"
        >
          <ExternalLink className="h-3.5 w-3.5" aria-hidden />
          {compacto ? null : 'Abrir no Drive'}
        </a>
      )}

      {destinos.length > 0 ? (
        <select
          aria-label={`Mover ${arquivo.nome} para outra pasta`}
          value=""
          disabled={ocupado}
          onChange={(evento) => {
            if (evento.target.value) {
              onMover(arquivo, evento.target.value);
            }
          }}
          className="h-8 max-w-[10rem] rounded-md border border-[#E5E7EB] bg-white px-2 text-[12px] text-[#4B5563] outline-none transition-colors hover:border-[#93C5FD] focus:border-[#2563EB] disabled:opacity-50"
        >
          <option value="">Mover para…</option>
          {destinos.map((pasta) => (
            <option key={pasta.id} value={pasta.id}>
              {pasta.nome}
            </option>
          ))}
        </select>
      ) : null}

      <button
        type="button"
        disabled={ocupado}
        onBlur={() => setConfirmar(false)}
        onClick={() => {
          if (!confirmar) {
            setConfirmar(true);
            return;
          }
          setConfirmar(false);
          onExcluir(arquivo);
        }}
        title={
          escolhidoNoDrive
            ? 'Tira o arquivo desta pasta. O original continua no seu Google Drive.'
            : 'Move o arquivo para a lixeira do seu Google Drive.'
        }
        aria-label={
          confirmar
            ? `Confirmar ${escolhidoNoDrive ? 'remoção' : 'exclusão'} de ${arquivo.nome}`
            : `${rotuloTirar} ${arquivo.nome}`
        }
        className={[
          'inline-flex h-8 items-center justify-center gap-1 rounded-md px-2 text-[12px] font-medium transition-colors disabled:opacity-50',
          confirmar
            ? 'bg-[#FEF2F2] font-semibold text-[#B91C1C] hover:bg-[#FEE2E2]'
            : 'text-[#6B7280] hover:bg-[#FEF2F2] hover:text-[#B91C1C]',
        ].join(' ')}
      >
        <Trash2 className="h-3.5 w-3.5" aria-hidden />
        {compacto ? (confirmar ? rotuloConfirma : null) : confirmar ? rotuloConfirma : rotuloTirar}
      </button>
    </div>
  );
}

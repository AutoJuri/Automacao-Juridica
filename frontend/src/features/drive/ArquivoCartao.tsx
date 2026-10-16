import { AlertTriangle } from 'lucide-react';

import { ArquivoAcoes } from './ArquivoAcoes';
import { ArquivoMarca } from './ArquivoMarca';
import { dataDoArquivo, rotuloTamanho, rotuloTipo } from './drive.format';
import type { ArquivoDrive, Pasta } from './drive.types';

interface ArquivoCartaoProps {
  arquivo: ArquivoDrive;
  destinos: Pasta[];
  ocupado: boolean;
  baixando: boolean;
  onBaixar: (arquivo: ArquivoDrive) => void;
  onMover: (arquivo: ArquivoDrive, pastaId: string) => void;
  onExcluir: (arquivo: ArquivoDrive) => void;
}

export function ArquivoCartao({
  arquivo,
  destinos,
  ocupado,
  baixando,
  onBaixar,
  onMover,
  onExcluir,
}: ArquivoCartaoProps) {
  return (
    <li className="flex min-w-0 flex-col rounded-xl border border-[#E5E7EB] bg-white p-2.5 shadow-sm">
      <ArquivoMarca nome={arquivo.nome} mimeType={arquivo.mime_type} tamanho="cartao" />
      <p className="mt-2 truncate text-[13px] font-semibold text-[#111827]" title={arquivo.nome}>
        {arquivo.nome}
      </p>
      <p className="mt-0.5 truncate text-[11px] text-[#6B7280]">
        {rotuloTipo(arquivo.mime_type, arquivo.nome)} · {rotuloTamanho(arquivo.tamanho)} ·{' '}
        {dataDoArquivo(arquivo.created_at)}
      </p>
      {arquivo.ausente_no_google ? (
        <p className="mt-1 flex items-center gap-1 text-[12px] font-medium text-[#B45309]">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
          Ausente no Google Drive
        </p>
      ) : null}
      <div className="mt-2 border-t border-[#F3F4F6] pt-1.5">
        <ArquivoAcoes
          arquivo={arquivo}
          destinos={destinos}
          ocupado={ocupado}
          baixando={baixando}
          compacto
          onBaixar={onBaixar}
          onMover={onMover}
          onExcluir={onExcluir}
        />
      </div>
    </li>
  );
}

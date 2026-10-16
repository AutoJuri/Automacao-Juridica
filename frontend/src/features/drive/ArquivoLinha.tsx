import { AlertTriangle } from 'lucide-react';

import { ArquivoAcoes } from './ArquivoAcoes';
import { ArquivoMarca } from './ArquivoMarca';
import { dataDoArquivo, rotuloOrigem, rotuloTamanho, rotuloTipo } from './drive.format';
import type { ArquivoDrive, Pasta } from './drive.types';

interface ArquivoLinhaProps {
  arquivo: ArquivoDrive;
  destinos: Pasta[];
  ocupado: boolean;
  baixando: boolean;
  onBaixar: (arquivo: ArquivoDrive) => void;
  onMover: (arquivo: ArquivoDrive, pastaId: string) => void;
  onExcluir: (arquivo: ArquivoDrive) => void;
}

export function ArquivoLinha({
  arquivo,
  destinos,
  ocupado,
  baixando,
  onBaixar,
  onMover,
  onExcluir,
}: ArquivoLinhaProps) {
  return (
    <li className="flex flex-col gap-3 rounded-xl border border-[#E5E7EB] bg-white px-4 py-3 shadow-sm lg:flex-row lg:items-center lg:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <ArquivoMarca nome={arquivo.nome} mimeType={arquivo.mime_type} tamanho="linha" />
        <div className="min-w-0">
          <p className="truncate text-[14px] font-semibold text-[#111827]" title={arquivo.nome}>
            {arquivo.nome}
          </p>
          <p className="mt-0.5 text-[12px] text-[#6B7280]">
            {rotuloTipo(arquivo.mime_type, arquivo.nome)} · {rotuloTamanho(arquivo.tamanho)} ·{' '}
            {rotuloOrigem(arquivo.origem)} · {dataDoArquivo(arquivo.created_at)}
          </p>
          {arquivo.ausente_no_google ? (
            <p className="mt-1 flex items-center gap-1 text-[12px] font-medium text-[#B45309]">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
              Não está mais no Google Drive. Você pode tirar da pasta.
            </p>
          ) : null}
        </div>
      </div>
      <ArquivoAcoes
        arquivo={arquivo}
        destinos={destinos}
        ocupado={ocupado}
        baixando={baixando}
        onBaixar={onBaixar}
        onMover={onMover}
        onExcluir={onExcluir}
      />
    </li>
  );
}

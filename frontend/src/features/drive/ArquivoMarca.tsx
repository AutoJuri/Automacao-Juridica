import { FileImage, FileText, FileType } from 'lucide-react';

import { grupoArquivo, type GrupoArquivo } from './drive.lista';

const FUNDO: Record<GrupoArquivo, string> = {
  pdf: 'bg-[#FEF2F2] text-[#B91C1C]',
  word: 'bg-[#EFF6FF] text-[#2563EB]',
  texto: 'bg-[#F3F4F6] text-[#4B5563]',
  imagem: 'bg-[#F0FDF4] text-[#166534]',
  outro: 'bg-[#EFF6FF] text-[#2563EB]',
};

interface ArquivoMarcaProps {
  nome: string;
  mimeType: string;
  /** `linha` é o quadradinho da lista. `cartao` é a faixa do modo grade. */
  tamanho: 'linha' | 'cartao';
}

export function ArquivoMarca({ nome, mimeType, tamanho }: ArquivoMarcaProps) {
  const grupo = grupoArquivo({ nome, mime_type: mimeType });
  const Icone = grupo === 'imagem' ? FileImage : grupo === 'texto' ? FileType : FileText;
  const grande = tamanho === 'cartao';

  return (
    <span
      className={[
        'inline-flex shrink-0 items-center justify-center',
        FUNDO[grupo],
        grande ? 'h-16 w-full rounded-lg' : 'mt-0.5 h-9 w-9 rounded-lg',
      ].join(' ')}
    >
      <Icone className={grande ? 'h-6 w-6' : 'h-4 w-4'} aria-hidden />
    </span>
  );
}

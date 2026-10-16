import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { FolderOpen, Search } from 'lucide-react';

import { mensagemDeErro } from '#/features/auth/auth.errors';
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando';
import { SecaoShell } from '#/features/secoes/SecaoShell';

import { GoogleDriveAviso } from './GoogleDriveAviso';
import { PastaCard } from './PastaCard';
import { PastaDialog } from './PastaDialog';
import { nomeCombina } from './drive.lista';
import { useExcluirPasta, usePastas } from './drive.queries';
import type { Pasta } from './drive.types';

const ERROS = {
  401: 'Sessão expirada. Entre novamente.',
};

export function DrivePage() {
  const navigate = useNavigate();
  const pastas = usePastas();
  const excluir = useExcluirPasta();
  const [dialogo, setDialogo] = useState<{
    aberto: boolean;
    pasta: Pasta | null;
  }>({
    aberto: false,
    pasta: null,
  });
  const [erroExcluir, setErroExcluir] = useState<string | null>(null);
  const [busca, setBusca] = useState('');

  const itens = pastas.data ?? [];
  const visiveis = itens.filter((pasta) => nomeCombina(pasta.nome, busca));

  function abrir(pastaId: string) {
    void navigate({ to: '/drive/$pastaId', params: { pastaId } });
  }

  async function excluirPasta(id: string) {
    setErroExcluir(null);
    try {
      await excluir.mutateAsync(id);
    } catch (falha) {
      setErroExcluir(mensagemDeErro(falha, { ...ERROS, 404: 'Essa pasta não existe mais.' }));
    }
  }

  return (
    <SecaoShell>
      <section className="mb-6 rounded-2xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB]">
              <FolderOpen className="h-5 w-5" aria-hidden />
            </span>
            <div>
              <p className="text-[11px] font-semibold tracking-[0.18em] text-[#2563EB] uppercase">
                Drive
              </p>
              <h1 className="text-xl font-semibold text-[#111827]">Cofre de documentos</h1>
              <p className="mt-1 text-sm text-[#6B7280]">
                Organize em pastas os documentos dos seus processos.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-[#F3F4F6] px-3 py-1 text-[12px] font-semibold text-[#374151]">
              {itens.length}
            </span>
            <button
              type="button"
              onClick={() => setDialogo({ aberto: true, pasta: null })}
              className="h-9 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] active:bg-[#1E40AF]"
            >
              Nova pasta
            </button>
          </div>
        </div>
        {erroExcluir ? <p className="mt-3 text-[13px] text-[#B91C1C]">{erroExcluir}</p> : null}
      </section>

      <GoogleDriveAviso />

      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-[13px] font-semibold tracking-wide text-[#111827] uppercase">
            Pastas
          </h2>
          {itens.length > 0 ? (
            <div className="relative w-56">
              <Search
                className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]"
                aria-hidden
              />
              <input
                type="search"
                value={busca}
                onChange={(evento) => setBusca(evento.target.value)}
                placeholder="Buscar pasta pelo nome"
                aria-label="Buscar pasta pelo nome"
                className="h-9 w-full rounded-lg border border-[#E5E7EB] bg-white pr-3 pl-8 text-[12px] text-[#111827] outline-none transition-colors placeholder:text-[#9CA3AF] hover:border-[#93C5FD] focus:border-[#2563EB]"
              />
            </div>
          ) : null}
        </div>
        {pastas.isLoading ? (
          <EstadoCarregando mensagem="Carregando pastas…" preencher={false} />
        ) : pastas.isError ? (
          <p className="text-sm text-[#6B7280]">{mensagemDeErro(pastas.error, ERROS)}</p>
        ) : itens.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[#D1D5DB] bg-white px-6 py-10 text-center">
            <p className="text-sm font-medium text-[#374151]">Nenhuma pasta ainda.</p>
            <p className="mt-1 text-[13px] text-[#6B7280]">
              Crie a primeira para separar os documentos de um processo.
            </p>
          </div>
        ) : visiveis.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[#D1D5DB] bg-white px-6 py-10 text-center">
            <p className="text-sm font-medium text-[#374151]">Nenhuma pasta com esse nome.</p>
            <button
              type="button"
              onClick={() => setBusca('')}
              className="mt-2 text-[13px] font-medium text-[#2563EB] hover:underline"
            >
              Ver todas
            </button>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {visiveis.map((pasta) => (
              <PastaCard
                key={pasta.id}
                pasta={pasta}
                excluindo={excluir.isPending}
                onAbrir={abrir}
                onEditar={(alvo) => setDialogo({ aberto: true, pasta: alvo })}
                onExcluir={(id) => {
                  void excluirPasta(id);
                }}
              />
            ))}
          </div>
        )}
      </section>

      <PastaDialog
        aberto={dialogo.aberto}
        pasta={dialogo.pasta}
        onAberto={(aberto) => setDialogo((atual) => ({ ...atual, aberto }))}
      />
    </SecaoShell>
  );
}

import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import { ChevronDown, Cloud, LayoutGrid, LayoutList, Loader2, Search, Upload } from 'lucide-react';

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando';

import { ArquivoCartao } from './ArquivoCartao';
import { ArquivoLinha } from './ArquivoLinha';
import { TIPOS_DE_ARQUIVO } from './drive.constants';
import { buscarTokenDoPicker } from './drive.api';
import { mensagemDoDrive } from './drive.errors';
import { problemaDoArquivo, rotuloArquivos } from './drive.format';
import {
  guardarVistaArquivos,
  lerVistaArquivos,
  nomeCombina,
  organizarArquivos,
  type FiltroTipoArquivo,
  type OrdemArquivo,
  type VistaArquivo,
} from './drive.lista';
import { ERRO_SCRIPT_DO_GOOGLE, escolherArquivosDoGoogle } from './drive.picker';
import {
  useArquivos,
  useBaixarArquivo,
  useEnviarArquivo,
  useExcluirArquivo,
  useMoverArquivo,
  usePastas,
  useStatusGoogle,
  useVincularArquivo,
} from './drive.queries';
import type { ArquivoDrive } from './drive.types';

interface ArquivosPastaProps {
  pastaId: string;
}

const FILTROS: { id: FiltroTipoArquivo; rotulo: string }[] = [
  { id: 'todos', rotulo: 'Todos' },
  { id: 'pdf', rotulo: 'PDF' },
  { id: 'word', rotulo: 'Word' },
  { id: 'texto', rotulo: 'Texto' },
  { id: 'imagem', rotulo: 'Imagem' },
];

const SELECT =
  'h-9 w-full appearance-none rounded-lg border border-[#E5E7EB] bg-white pr-8 pl-3 text-[12px] font-medium text-[#374151] outline-none transition-colors hover:border-[#93C5FD] focus:border-[#2563EB]';

const CAMPO_BUSCA =
  'h-9 w-full rounded-lg border border-[#E5E7EB] bg-white pr-3 pl-8 text-[12px] text-[#111827] outline-none transition-colors placeholder:text-[#9CA3AF] hover:border-[#93C5FD] focus:border-[#2563EB]';

function salvarNoComputador(blob: Blob, nome: string) {
  const url = URL.createObjectURL(blob);
  const ancora = document.createElement('a');
  ancora.href = url;
  ancora.download = nome;
  document.body.appendChild(ancora);
  ancora.click();
  ancora.remove();
  URL.revokeObjectURL(url);
}

export function ArquivosPasta({ pastaId }: ArquivosPastaProps) {
  const status = useStatusGoogle();
  const arquivos = useArquivos(pastaId);
  const pastas = usePastas();
  const enviar = useEnviarArquivo();
  const vincular = useVincularArquivo();
  const baixar = useBaixarArquivo();
  const mover = useMoverArquivo();
  const excluir = useExcluirArquivo();

  const entrada = useRef<HTMLInputElement>(null);
  const [arrastando, setArrastando] = useState(false);
  const [abrindoSeletor, setAbrindoSeletor] = useState(false);
  const [enviando, setEnviando] = useState<string | null>(null);
  const [baixandoId, setBaixandoId] = useState<string | null>(null);
  const [avisos, setAvisos] = useState<string[]>([]);
  const [ordem, setOrdem] = useState<OrdemArquivo>('data-desc');
  const [filtro, setFiltro] = useState<FiltroTipoArquivo>('todos');
  const [busca, setBusca] = useState('');
  const [vista, setVista] = useState<VistaArquivo>(lerVistaArquivos);

  const conectado = status.data?.conectado ?? false;
  const seletorPronto = conectado && (status.data?.picker_configurado ?? false);
  const itens = arquivos.data ?? [];
  const visiveis = organizarArquivos(itens, filtro, ordem).filter((arquivo) =>
    nomeCombina(arquivo.nome, busca),
  );
  const destinos = (pastas.data ?? []).filter((pasta) => pasta.id !== pastaId);
  const ocupado =
    enviando !== null ||
    abrindoSeletor ||
    vincular.isPending ||
    mover.isPending ||
    excluir.isPending;

  async function enviarTodos(lista: File[]) {
    if (lista.length === 0 || !conectado) {
      return;
    }
    const problemas: string[] = [];
    for (const arquivo of lista) {
      const recusa = problemaDoArquivo(arquivo);
      if (recusa) {
        problemas.push(recusa);
        continue;
      }
      setEnviando(arquivo.name);
      try {
        await enviar.mutateAsync({ pastaId, arquivo });
      } catch (falha) {
        problemas.push(`“${arquivo.name}”: ${mensagemDoDrive(falha)}`);
      }
    }
    setEnviando(null);
    setAvisos(problemas);
  }

  function aoSoltar(evento: DragEvent<HTMLDivElement>) {
    evento.preventDefault();
    setArrastando(false);
    if (conectado && !ocupado) {
      void enviarTodos(Array.from(evento.dataTransfer.files));
    }
  }

  async function escolherNoGoogle() {
    setAvisos([]);
    setAbrindoSeletor(true);
    const problemas: string[] = [];
    try {
      const ids = await escolherArquivosDoGoogle(buscarTokenDoPicker);
      for (const googleFileId of ids) {
        try {
          await vincular.mutateAsync({ pastaId, googleFileId });
        } catch (falha) {
          problemas.push(mensagemDoDrive(falha));
        }
      }
    } catch (falha) {
      problemas.push(
        falha instanceof Error && falha.message === ERRO_SCRIPT_DO_GOOGLE
          ? 'Não foi possível carregar o seletor do Google. Verifique a conexão e tente de novo.'
          : mensagemDoDrive(falha),
      );
    } finally {
      setAbrindoSeletor(false);
    }
    setAvisos(problemas);
  }

  async function baixarArquivo(arquivo: ArquivoDrive) {
    setAvisos([]);
    setBaixandoId(arquivo.id);
    try {
      const conteudo = await baixar.mutateAsync(arquivo.id);
      salvarNoComputador(conteudo, arquivo.nome);
    } catch (falha) {
      setAvisos([
        `“${arquivo.nome}”: ${mensagemDoDrive(falha, { 404: 'O arquivo não está mais no Google Drive.' })}`,
      ]);
    } finally {
      setBaixandoId(null);
    }
  }

  async function moverArquivo(arquivo: ArquivoDrive, destino: string) {
    setAvisos([]);
    try {
      await mover.mutateAsync({ id: arquivo.id, pastaId: destino });
    } catch (falha) {
      setAvisos([`“${arquivo.nome}”: ${mensagemDoDrive(falha)}`]);
    }
  }

  async function excluirArquivo(arquivo: ArquivoDrive) {
    setAvisos([]);
    try {
      await excluir.mutateAsync(arquivo.id);
    } catch (falha) {
      setAvisos([`“${arquivo.nome}”: ${mensagemDoDrive(falha)}`]);
    }
  }

  return (
    <section>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-[13px] font-semibold tracking-wide text-[#111827] uppercase">
          Arquivos
          {arquivos.isSuccess ? (
            <span className="ml-2 font-normal tracking-normal text-[#6B7280] normal-case">
              {rotuloArquivos(visiveis.length)}
            </span>
          ) : null}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          {seletorPronto ? (
            <button
              type="button"
              disabled={ocupado}
              onClick={() => {
                void escolherNoGoogle();
              }}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-semibold text-[#374151] transition-colors hover:border-[#93C5FD] hover:bg-[#EFF6FF] hover:text-[#2563EB] disabled:opacity-50"
            >
              {abrindoSeletor ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <Cloud className="h-3.5 w-3.5" aria-hidden />
              )}
              Escolher do Google Drive
            </button>
          ) : null}
          <button
            type="button"
            disabled={!conectado || ocupado}
            title={conectado ? undefined : 'Conecte o Google Drive para enviar arquivos'}
            onClick={() => entrada.current?.click()}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] active:bg-[#1E40AF] disabled:opacity-50"
          >
            {enviando ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : (
              <Upload className="h-3.5 w-3.5" aria-hidden />
            )}
            Enviar arquivo
          </button>
          <input
            ref={entrada}
            type="file"
            multiple
            hidden
            accept={TIPOS_DE_ARQUIVO.flatMap((tipo) => [...tipo.extensoes]).join(',')}
            onChange={(evento) => {
              const escolhidos = Array.from(evento.target.files ?? []);
              evento.target.value = '';
              void enviarTodos(escolhidos);
            }}
          />
        </div>
      </div>

      {enviando ? (
        <p role="status" className="mb-3 text-[13px] text-[#2563EB]">
          Enviando “{enviando}”…
        </p>
      ) : null}
      {avisos.length > 0 ? (
        <ul
          role="alert"
          className="mb-3 space-y-1 rounded-lg border border-[#FECACA] bg-[#FEF2F2] px-3 py-2"
        >
          {avisos.map((aviso) => (
            <li key={aviso} className="text-[13px] text-[#B91C1C]">
              {aviso}
            </li>
          ))}
        </ul>
      ) : null}

      {arquivos.isLoading ? (
        <EstadoCarregando mensagem="Carregando arquivos…" preencher={false} />
      ) : arquivos.isError ? (
        <p className="text-sm text-[#6B7280]">{mensagemDoDrive(arquivos.error)}</p>
      ) : (
        <div
          onDragOver={(evento) => {
            if (conectado) {
              evento.preventDefault();
              setArrastando(true);
            }
          }}
          onDragLeave={() => setArrastando(false)}
          onDrop={aoSoltar}
          className={[
            'rounded-xl transition-colors',
            arrastando ? 'bg-[#EFF6FF] outline-2 outline-dashed outline-[#2563EB]' : '',
          ].join(' ')}
        >
          {itens.length > 0 ? (
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <div className="relative w-44">
                <Search
                  className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]"
                  aria-hidden
                />
                <input
                  type="search"
                  value={busca}
                  onChange={(evento) => setBusca(evento.target.value)}
                  placeholder="Buscar pelo nome"
                  aria-label="Buscar arquivo pelo nome"
                  className={CAMPO_BUSCA}
                />
              </div>
              <div className="relative w-40">
                <select
                  aria-label="Ordenar arquivos"
                  value={ordem}
                  onChange={(evento) => setOrdem(evento.target.value as OrdemArquivo)}
                  className={SELECT}
                >
                  <option value="nome-asc">Nome (A–Z)</option>
                  <option value="nome-desc">Nome (Z–A)</option>
                  <option value="data-desc">Mais recentes</option>
                  <option value="data-asc">Mais antigos</option>
                </select>
                <ChevronDown
                  className="pointer-events-none absolute top-1/2 right-2.5 h-3.5 w-3.5 -translate-y-1/2 text-[#6B7280]"
                  aria-hidden
                />
              </div>
              <div className="flex flex-wrap gap-1" role="group" aria-label="Tipo de documento">
                {FILTROS.map((opcao) => {
                  const ativo = filtro === opcao.id;
                  return (
                    <button
                      key={opcao.id}
                      type="button"
                      aria-pressed={ativo}
                      onClick={() => setFiltro(opcao.id)}
                      className={[
                        'h-9 rounded-lg px-2.5 text-[12px] font-semibold transition-colors',
                        ativo
                          ? 'bg-[#2563EB] text-white'
                          : 'border border-[#E5E7EB] bg-white text-[#4B5563] hover:border-[#93C5FD] hover:text-[#2563EB]',
                      ].join(' ')}
                    >
                      {opcao.rotulo}
                    </button>
                  );
                })}
              </div>
              <div
                className="ml-auto inline-flex rounded-lg border border-[#E5E7EB] bg-white p-0.5"
                role="group"
                aria-label="Visualização"
              >
                <button
                  type="button"
                  aria-pressed={vista === 'lista'}
                  aria-label="Ver em lista"
                  title="Lista"
                  onClick={() => {
                    setVista('lista');
                    guardarVistaArquivos('lista');
                  }}
                  className={[
                    'inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors',
                    vista === 'lista'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#6B7280] hover:bg-[#F3F4F6]',
                  ].join(' ')}
                >
                  <LayoutList className="h-4 w-4" aria-hidden />
                </button>
                <button
                  type="button"
                  aria-pressed={vista === 'grade'}
                  aria-label="Ver em grade"
                  title="Grade"
                  onClick={() => {
                    setVista('grade');
                    guardarVistaArquivos('grade');
                  }}
                  className={[
                    'inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors',
                    vista === 'grade'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#6B7280] hover:bg-[#F3F4F6]',
                  ].join(' ')}
                >
                  <LayoutGrid className="h-4 w-4" aria-hidden />
                </button>
              </div>
            </div>
          ) : null}
          {itens.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[#D1D5DB] bg-white px-6 py-12 text-center">
              <p className="text-sm font-medium text-[#374151]">
                {conectado
                  ? 'Nenhum arquivo nesta pasta.'
                  : 'Conecte o Google Drive para guardar arquivos.'}
              </p>
              <p className="mx-auto mt-1 max-w-md text-[13px] text-[#6B7280]">
                {conectado
                  ? 'Arraste arquivos até aqui ou use “Enviar arquivo”.'
                  : status.data?.configurado
                    ? 'Use o cartão acima. Os arquivos ficam na sua própria conta do Google.'
                    : 'A conexão ainda não foi configurada neste servidor.'}
              </p>
              <ul
                className="mt-4 flex flex-wrap justify-center gap-2"
                aria-label="Tipos de arquivo aceitos"
              >
                {TIPOS_DE_ARQUIVO.map((tipo) => (
                  <li
                    key={tipo.rotulo}
                    className="rounded-full bg-[#F3F4F6] px-2.5 py-1 text-[11px] font-medium text-[#4B5563]"
                  >
                    {tipo.rotulo} · {tipo.extensoes.join(' ')}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[11px] text-[#9CA3AF]">Até 25 MB por arquivo.</p>
            </div>
          ) : visiveis.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[#D1D5DB] bg-white px-6 py-10 text-center">
              <p className="text-sm font-medium text-[#374151]">
                {busca.trim() ? 'Nenhum arquivo com esse nome.' : 'Nenhum arquivo deste tipo.'}
              </p>
              <button
                type="button"
                onClick={() => {
                  setBusca('');
                  setFiltro('todos');
                }}
                className="mt-2 text-[13px] font-medium text-[#2563EB] hover:underline"
              >
                Ver todos
              </button>
            </div>
          ) : (
            <ul
              className={
                vista === 'grade'
                  ? 'grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                  : 'space-y-2'
              }
            >
              {visiveis.map((arquivo) => {
                const Cartao = vista === 'grade' ? ArquivoCartao : ArquivoLinha;
                return (
                  <Cartao
                    key={arquivo.id}
                    arquivo={arquivo}
                    destinos={destinos}
                    ocupado={ocupado}
                    baixando={baixandoId === arquivo.id}
                    onBaixar={(alvo) => {
                      void baixarArquivo(alvo);
                    }}
                    onMover={(alvo, destino) => {
                      void moverArquivo(alvo, destino);
                    }}
                    onExcluir={(alvo) => {
                      void excluirArquivo(alvo);
                    }}
                  />
                );
              })}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

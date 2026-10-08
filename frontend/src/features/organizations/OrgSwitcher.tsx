import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useRouterState } from '@tanstack/react-router'
import { Building2, Check, ChevronDown, Plus } from 'lucide-react'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { useOrgStore } from '#/store/org.store'
import { criarOrganizacao, listarOrganizacoes } from './organizations.api'
import { ORGANIZATIONS_QUERY_KEY } from './organizations.constants'

export function OrgSwitcher() {
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const queryClient = useQueryClient()
  const ativaId = useOrgStore((s) => s.activeOrganizationId)
  const setAtiva = useOrgStore((s) => s.setActiveOrganizationId)
  const [aberto, setAberto] = useState(false)
  const [criando, setCriando] = useState(false)
  const [nome, setNome] = useState('')
  const painelRef = useRef<HTMLDivElement>(null)

  const lista = useQuery({
    queryKey: ORGANIZATIONS_QUERY_KEY,
    queryFn: listarOrganizacoes,
  })

  const organizacoes = lista.data ?? []
  const ativa = organizacoes.find((org) => org.id === ativaId) ?? null

  useEffect(() => {
    if (!lista.data || !ativaId) {
      return
    }
    if (!lista.data.some((org) => org.id === ativaId)) {
      setAtiva(null)
    }
  }, [lista.data, ativaId, setAtiva])

  useEffect(() => {
    if (!aberto) {
      return
    }
    function fechar(evento: MouseEvent) {
      if (painelRef.current && !painelRef.current.contains(evento.target as Node)) {
        setAberto(false)
        setCriando(false)
      }
    }
    document.addEventListener('mousedown', fechar)
    return () => document.removeEventListener('mousedown', fechar)
  }, [aberto])

  const criar = useMutation({
    mutationFn: () => criarOrganizacao(nome.trim()),
    onSuccess: (org) => {
      setAtiva(org.id)
      setNome('')
      setCriando(false)
      setAberto(false)
      void queryClient.invalidateQueries({ queryKey: ORGANIZATIONS_QUERY_KEY })
      void navigate({ to: '/organizacoes/$orgId', params: { orgId: org.id } })
    },
  })

  function escolher(id: string | null) {
    setAtiva(id)
    setAberto(false)
    if (!pathname.startsWith('/organizacoes/')) {
      return
    }
    if (id) {
      void navigate({ to: '/organizacoes/$orgId', params: { orgId: id } })
    } else {
      void navigate({ to: '/' })
    }
  }

  const erro = criar.error
    ? mensagemDeErro(criar.error, { 422: 'Informe um nome com pelo menos 2 caracteres.' })
    : null

  return (
    <div className="relative" ref={painelRef}>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setAberto((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={aberto}
        className="h-9 max-w-[200px] gap-1.5 px-3 text-[13px] font-medium text-[#4B5563] hover:text-[#111827] hover:bg-[#F3F4F6] border border-[#E5E7EB]"
      >
        <Building2 className="w-3.5 h-3.5 shrink-0" />
        <span className="truncate">{ativa ? ativa.name : 'Pessoal'}</span>
        <ChevronDown className="w-3.5 h-3.5 shrink-0 opacity-70" />
      </Button>

      {aberto ? (
        <div className="absolute right-0 mt-2 w-[280px] rounded-xl border border-[#E5E7EB] bg-white shadow-lg z-50 overflow-hidden">
          <ul className="py-1" role="listbox" aria-label="Organização ativa">
            <li>
              <button
                type="button"
                role="option"
                aria-selected={ativa === null}
                onClick={() => escolher(null)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-[#111827] hover:bg-[#F8F9FC]"
              >
                <Check className={ativa === null ? 'w-3.5 h-3.5 text-[#3B5BDB]' : 'w-3.5 h-3.5 opacity-0'} />
                Pessoal
              </button>
            </li>
            {organizacoes.map((org) => (
              <li key={org.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={ativa?.id === org.id}
                  onClick={() => escolher(org.id)}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-[#111827] hover:bg-[#F8F9FC]"
                >
                  <Check
                    className={
                      ativa?.id === org.id ? 'w-3.5 h-3.5 text-[#3B5BDB]' : 'w-3.5 h-3.5 opacity-0'
                    }
                  />
                  <span className="truncate">{org.name}</span>
                </button>
              </li>
            ))}
          </ul>

          <div className="border-t border-[#E5E7EB] p-2 space-y-1">
            {ativa ? (
              <button
                type="button"
                onClick={() => {
                  setAberto(false)
                  void navigate({ to: '/organizacoes/$orgId', params: { orgId: ativa.id } })
                }}
                className="w-full text-left px-2 py-1.5 text-[13px] font-medium text-[#3B5BDB] hover:bg-[#F8F9FC] rounded-md"
              >
                Membros
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => {
                setAberto(false)
                void navigate({ to: '/convites' })
              }}
              className="w-full text-left px-2 py-1.5 text-[13px] text-[#374151] hover:bg-[#F8F9FC] rounded-md"
            >
              Convites recebidos
            </button>
            {criando ? (
              <form
                className="space-y-2 px-1 pt-1"
                onSubmit={(evento) => {
                  evento.preventDefault()
                  if (nome.trim().length >= 2) {
                    criar.mutate()
                  }
                }}
              >
                <Input
                  value={nome}
                  onChange={(evento) => setNome(evento.target.value)}
                  placeholder="Nome do escritório"
                  maxLength={255}
                  autoFocus
                  className="h-9 text-[13px]"
                />
                {erro ? <p className="text-[11px] text-[#DC2626]">{erro}</p> : null}
                <Button
                  type="submit"
                  disabled={criar.isPending || nome.trim().length < 2}
                  className="w-full h-8 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white text-[12px]"
                >
                  {criar.isPending ? 'Criando...' : 'Criar organização'}
                </Button>
              </form>
            ) : (
              <button
                type="button"
                onClick={() => setCriando(true)}
                className="flex w-full items-center gap-2 px-2 py-1.5 text-[13px] text-[#374151] hover:bg-[#F8F9FC] rounded-md"
              >
                <Plus className="w-3.5 h-3.5" />
                Criar organização
              </button>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}

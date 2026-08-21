import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { KeyRound, Loader2, RefreshCw, ShieldAlert, ShieldCheck, Trash2 } from 'lucide-react'
import { Controller, useForm } from 'react-hook-form'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { MUITAS_TENTATIVAS, mensagemDeErro } from '#/features/auth/auth.errors'
import { FieldError, FormError } from '#/features/auth/AuthFormFeedback'
import {
  buscarStatusCredenciais,
  removerCredencialEsaj,
  revalidarCredencialEsaj,
  salvarCredencialEsaj,
} from './credentials.api'
import { CREDENTIALS_STATUS_QUERY_KEY } from './credentials.constants'
import { esajCredentialSchema, type EsajCredentialFormValues } from './credentials.schemas'
import type { SessionStatus } from './credentials.types'

/** Mensagem final por `session_status` — nunca expõe detalhe técnico do login. */
const MENSAGENS_SESSION_STATUS: Record<Exclude<SessionStatus, 'reauth_pendente'>, string> = {
  ativo: 'Credencial validada com sucesso no e-SAJ.',
  bloqueado:
    'O e-SAJ bloqueou temporariamente as tentativas de login. Aguarde alguns minutos e tente revalidar.',
  credencial_invalida:
    'CPF ou senha não foram aceitos pelo e-SAJ. Remova e cadastre as credenciais novamente.',
  email_desconectado:
    'Não foi possível capturar o código de verificação: conecte um e-mail para continuar.',
  portal_indisponivel:
    'O e-SAJ está indisponível ou demorou para responder. Tente revalidar em alguns minutos.',
  codigo_nao_encontrado:
    'Não encontramos o código de verificação no e-mail a tempo. Confira a caixa de entrada/spam e clique em Revalidar.',
}

/** Só `reauth_pendente` significa validação em andamento — `null` é "ainda não validou". */
function estaValidando(status: SessionStatus | null | undefined): boolean {
  return status === 'reauth_pendente'
}

function formatarCpf(valor: string): string {
  const digitos = valor.replace(/\D/g, '').slice(0, 11)
  const partes = [digitos.slice(0, 3), digitos.slice(3, 6), digitos.slice(6, 9)].filter(Boolean)
  let formatado = partes.join('.')
  if (digitos.length > 9) {
    formatado += `-${digitos.slice(9, 11)}`
  }
  return formatado
}

export function EsajCredentialForm() {
  const queryClient = useQueryClient()
  const statusQuery = useQuery({
    queryKey: CREDENTIALS_STATUS_QUERY_KEY,
    queryFn: buscarStatusCredenciais,
    refetchInterval: (query) => {
      const dados = query.state.data
      const emValidacao = dados?.cadastrado && estaValidando(dados.session_status)
      return emValidacao ? 3000 : false
    },
  })

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<EsajCredentialFormValues>({
    resolver: zodResolver(esajCredentialSchema),
    defaultValues: { cpf: '', senha: '' },
  })

  const salvar = useMutation({
    mutationFn: salvarCredencialEsaj,
    onSuccess: (status) => {
      queryClient.setQueryData(CREDENTIALS_STATUS_QUERY_KEY, status)
      reset()
    },
  })

  const remover = useMutation({
    mutationFn: removerCredencialEsaj,
    onSuccess: (status) => {
      queryClient.setQueryData(CREDENTIALS_STATUS_QUERY_KEY, status)
    },
  })

  const revalidar = useMutation({
    mutationFn: revalidarCredencialEsaj,
    onSuccess: (status) => {
      queryClient.setQueryData(CREDENTIALS_STATUS_QUERY_KEY, status)
    },
  })

  const erroSalvar = salvar.error
    ? mensagemDeErro(salvar.error, {
        422: 'Verifique o CPF informado.',
        429: MUITAS_TENTATIVAS,
      })
    : null

  const erroRevalidar = revalidar.error
    ? mensagemDeErro(revalidar.error, { 429: MUITAS_TENTATIVAS })
    : null

  const cadastrado = statusQuery.data?.cadastrado ?? false
  const emailConectado = statusQuery.data?.email_conectado ?? false
  const sessionStatus = statusQuery.data?.session_status ?? null
  const sessaoExpirada = statusQuery.data?.sessao_expirada ?? false
  const validando = cadastrado && estaValidando(sessionStatus)
  const falhou = cadastrado && !validando && sessionStatus !== 'ativo' && sessionStatus !== null
  const aguardandoPrimeiraValidacao = cadastrado && sessionStatus === null
  const permiteRevalidar =
    (falhou && sessionStatus !== 'credencial_invalida') ||
    (aguardandoPrimeiraValidacao && emailConectado) ||
    (sessionStatus === 'ativo' && sessaoExpirada && emailConectado)

  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2.5 mb-1">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#EEF2FF]">
          <KeyRound className="w-4 h-4 text-[#3B5BDB]" />
        </div>
        <h2 className="text-[15px] font-semibold text-[#111827]">Credenciais do e-SAJ</h2>
      </div>
      <p className="text-xs text-[#6B7280] mb-5 leading-relaxed">
        CPF e senha usados no login do e-SAJ (TJSP). Guardamos tudo criptografado — nunca exibimos
        a senha de volta, e o CPF só aparece parcialmente mascarado.
      </p>

      {statusQuery.isLoading ? (
        <p className="text-sm text-[#9CA3AF]">Carregando...</p>
      ) : cadastrado ? (
        <div className="space-y-4">
          <div className="flex items-center gap-2.5 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3">
            <KeyRound className="w-4 h-4 shrink-0 text-[#6B7280]" />
            <div>
              <p className="text-sm font-medium text-[#111827]">Credencial cadastrada</p>
              <p className="text-xs text-[#6B7280]">CPF {statusQuery.data?.cpf_mascarado}</p>
            </div>
          </div>

          {validando ? (
            <div className="flex items-center gap-2.5 rounded-lg border border-[#BFDBFE] bg-[#EFF6FF] px-4 py-3">
              <Loader2 className="w-4 h-4 shrink-0 animate-spin text-[#2563EB]" />
              <p className="text-sm text-[#1E40AF]">
                Validando suas credenciais no e-SAJ... pode levar até 1 minuto.
              </p>
            </div>
          ) : sessionStatus === 'ativo' && sessaoExpirada ? (
            <div className="flex items-start gap-2.5 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] px-4 py-3">
              <ShieldAlert className="w-4 h-4 shrink-0 text-[#D97706] mt-0.5" />
              <p className="text-sm text-[#92400E]">
                A sessão do e-SAJ expirou. Clique em Revalidar para renovar o acesso — CPF e senha
                já estão cadastrados.
              </p>
            </div>
          ) : sessionStatus === 'ativo' ? (
            <div className="flex items-center gap-2.5 rounded-lg border border-[#DCFCE7] bg-[#F0FDF4] px-4 py-3">
              <ShieldCheck className="w-4 h-4 shrink-0 text-[#16A34A]" />
              <p className="text-sm font-medium text-[#166534]">{MENSAGENS_SESSION_STATUS.ativo}</p>
            </div>
          ) : falhou ? (
            <div className="flex items-start gap-2.5 rounded-lg border border-[#FECACA] bg-[#FEF2F2] px-4 py-3">
              <ShieldAlert className="w-4 h-4 shrink-0 text-[#DC2626] mt-0.5" />
              <p className="text-sm text-[#991B1B]">
                {MENSAGENS_SESSION_STATUS[sessionStatus as Exclude<SessionStatus, 'reauth_pendente'>]}
              </p>
            </div>
          ) : aguardandoPrimeiraValidacao && !emailConectado ? (
            <div className="flex items-start gap-2.5 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] px-4 py-3">
              <ShieldAlert className="w-4 h-4 shrink-0 text-[#D97706] mt-0.5" />
              <p className="text-sm text-[#92400E]">
                Credenciais salvas. Conecte um e-mail abaixo para validar o login no e-SAJ.
              </p>
            </div>
          ) : aguardandoPrimeiraValidacao && emailConectado ? (
            <div className="flex items-start gap-2.5 rounded-lg border border-[#BFDBFE] bg-[#EFF6FF] px-4 py-3">
              <ShieldAlert className="w-4 h-4 shrink-0 text-[#2563EB] mt-0.5" />
              <p className="text-sm text-[#1E40AF]">
                E-mail conectado. Clique em Revalidar para testar o login no e-SAJ.
              </p>
            </div>
          ) : null}

          <FormError message={erroRevalidar} />

          <div className="flex flex-wrap gap-2">
            {permiteRevalidar && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => revalidar.mutate()}
                disabled={revalidar.isPending || validando}
                className="gap-1.5 border-[#E5E7EB] text-[#374151] hover:bg-[#F9FAFB]"
              >
                {revalidar.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                Revalidar
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => remover.mutate()}
              disabled={remover.isPending || validando}
              className="gap-1.5 text-[#DC2626] border-[#FECACA] hover:bg-[#FEF2F2] hover:text-[#DC2626]"
            >
              {remover.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Trash2 className="w-3.5 h-3.5" />
              )}
              Remover credenciais
            </Button>
          </div>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit((dados) => salvar.mutate(dados))}
          className="space-y-4"
          noValidate
        >
          <FormError message={erroSalvar} />

          <div className="space-y-1.5">
            <Label
              htmlFor="esaj-cpf"
              className="text-xs font-medium text-[#374151] uppercase tracking-wide"
            >
              CPF
            </Label>
            <Controller
              control={control}
              name="cpf"
              render={({ field }) => (
                <Input
                  id="esaj-cpf"
                  inputMode="numeric"
                  autoComplete="off"
                  placeholder="000.000.000-00"
                  aria-invalid={errors.cpf !== undefined}
                  value={formatarCpf(field.value)}
                  onChange={(e) => field.onChange(formatarCpf(e.target.value))}
                  onBlur={field.onBlur}
                  className="h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
                />
              )}
            />
            <FieldError message={errors.cpf?.message} />
          </div>

          <div className="space-y-1.5">
            <Label
              htmlFor="esaj-senha"
              className="text-xs font-medium text-[#374151] uppercase tracking-wide"
            >
              Senha do e-SAJ
            </Label>
            <Input
              id="esaj-senha"
              type="password"
              autoComplete="new-password"
              aria-invalid={errors.senha !== undefined}
              {...register('senha')}
              className="h-11 border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB]"
            />
            <FieldError message={errors.senha?.message} />
          </div>

          <Button
            type="submit"
            disabled={salvar.isPending}
            className="h-10 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm disabled:opacity-70"
          >
            {salvar.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Salvando...
              </>
            ) : (
              'Salvar credenciais'
            )}
          </Button>
        </form>
      )}
    </div>
  )
}

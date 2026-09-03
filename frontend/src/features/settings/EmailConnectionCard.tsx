import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Mail, Unplug } from 'lucide-react'

import { Button } from '#/components/ui/button'
import { MUITAS_TENTATIVAS, mensagemDeErro } from '#/features/auth/auth.errors'
import { FormError } from '#/features/auth/AuthFormFeedback'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import {
  buscarStatusCredenciais,
  buscarUrlDeAutorizacaoEmail,
  desconectarEmail,
} from './credentials.api'
import { CREDENTIALS_STATUS_QUERY_KEY } from './credentials.constants'
import type { EmailProvider } from './credentials.types'

const PROVIDER_LABEL: Record<EmailProvider, string> = {
  gmail: 'Gmail',
  outlook: 'Outlook',
}

export function EmailConnectionCard() {
  const queryClient = useQueryClient()
  const statusQuery = useQuery({
    queryKey: CREDENTIALS_STATUS_QUERY_KEY,
    queryFn: buscarStatusCredenciais,
  })

  const conectar = useMutation({
    mutationFn: buscarUrlDeAutorizacaoEmail,
    onSuccess: ({ authorize_url }) => {
      // Navegação de página inteira, não SPA: o consentimento acontece no
      // domínio do provedor, fora do nosso app.
      window.location.href = authorize_url
    },
  })

  const desconectar = useMutation({
    mutationFn: desconectarEmail,
    onSuccess: (status) => {
      queryClient.setQueryData(CREDENTIALS_STATUS_QUERY_KEY, status)
    },
  })

  const erroConectar = conectar.error
    ? mensagemDeErro(conectar.error, {
        400: 'Cadastre as credenciais do e-SAJ antes de conectar o e-mail.',
        429: MUITAS_TENTATIVAS,
        503: 'Conexão com este provedor ainda não está disponível.',
      })
    : null

  const cadastrado = statusQuery.data?.cadastrado ?? false
  const conectado = statusQuery.data?.email_conectado ?? false
  const provider = statusQuery.data?.email_provider ?? null

  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2.5 mb-1">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#EEF2FF]">
          <Mail className="w-4 h-4 text-[#3B5BDB]" />
        </div>
        <h2 className="text-[15px] font-semibold text-[#111827]">Conexão de e-mail</h2>
      </div>
      <p className="text-xs text-[#6B7280] mb-5 leading-relaxed">
        Usado só para ler (nunca enviar ou apagar) o código de verificação que o e-SAJ envia por
        e-mail durante o login. Conecte depois de cadastrar as credenciais do e-SAJ acima.
      </p>

      <FormError message={erroConectar} />

      {statusQuery.isLoading ? (
        <EstadoCarregando mensagem="Carregando..." compacto />
      ) : !cadastrado ? (
        <p className="text-xs text-[#B45309] bg-[#FFFBEB] border border-[#FDE68A] rounded-lg px-3 py-2.5 mt-3">
          Cadastre as credenciais do e-SAJ antes de conectar o e-mail.
        </p>
      ) : conectado && provider ? (
        <div className="space-y-4 mt-3">
          <div className="flex items-center justify-between rounded-lg border border-[#DCFCE7] bg-[#F0FDF4] px-4 py-3">
            <p className="text-sm font-medium text-[#166534]">
              {PROVIDER_LABEL[provider]} conectado
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => desconectar.mutate()}
            disabled={desconectar.isPending}
            className="gap-1.5 text-[#DC2626] border-[#FECACA] hover:bg-[#FEF2F2] hover:text-[#DC2626]"
          >
            {desconectar.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Unplug className="w-3.5 h-3.5" />
            )}
            Desconectar
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3 mt-3">
          <Button
            type="button"
            onClick={() => conectar.mutate('gmail')}
            disabled={conectar.isPending}
            className="h-10 gap-1.5 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white font-medium text-sm disabled:opacity-70"
          >
            {conectar.isPending && conectar.variables === 'gmail' && (
              <Loader2 className="w-4 h-4 animate-spin" />
            )}
            Conectar Gmail
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => conectar.mutate('outlook')}
            disabled={conectar.isPending}
            className="h-10 gap-1.5 border-[#E5E7EB] text-[#374151] font-medium text-sm disabled:opacity-70"
          >
            {conectar.isPending && conectar.variables === 'outlook' && (
              <Loader2 className="w-4 h-4 animate-spin" />
            )}
            Conectar Outlook
          </Button>
        </div>
      )}
    </div>
  )
}

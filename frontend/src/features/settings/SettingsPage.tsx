import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'

import { AppChrome } from '#/features/processos/AppChrome'
import { FormError, FormSuccess } from '#/features/auth/AuthFormFeedback'
import { CREDENTIALS_STATUS_QUERY_KEY } from './credentials.constants'
import { EmailConnectionCard } from './EmailConnectionCard'
import { EsajCredentialForm } from './EsajCredentialForm'

interface SettingsPageProps {
  /** Retorno do callback OAuth2 (`?email=conectado|erro`) — ver rota `/configuracoes`. */
  emailFeedback?: 'conectado' | 'erro'
}

export function SettingsPage({ emailFeedback }: SettingsPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!emailFeedback) {
      return
    }
    // O status mudou no backend durante o callback; a query em cache está
    // desatualizada até essa invalidação.
    queryClient.invalidateQueries({ queryKey: CREDENTIALS_STATUS_QUERY_KEY })
    // Remove o parâmetro da URL para não repetir o feedback num refresh manual.
    navigate({ to: '/configuracoes', search: {}, replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emailFeedback])

  return (
    <AppChrome contentClassName="flex-1 overflow-y-auto px-5 sm:px-8 lg:px-10 xl:px-14 py-8">
        <div className="max-w-2xl mx-auto space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-[#111827]">Configurações</h1>
            <p className="mt-1 text-sm text-[#6B7280]">
              Credenciais do e-SAJ e conexão de e-mail usadas para automatizar o acompanhamento
              dos seus processos.
            </p>
          </div>

          {emailFeedback === 'conectado' && (
            <FormSuccess message="E-mail conectado com sucesso." />
          )}
          {emailFeedback === 'erro' && (
            <FormError message="Não foi possível conectar o e-mail. Tente novamente." />
          )}

          <EsajCredentialForm />
          <EmailConnectionCard />
        </div>
    </AppChrome>
  )
}

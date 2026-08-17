# Módulo: Login Automatizado no e-SAJ (Playwright)

> Última atualização: 2026-08-17 (hardening)
> Camada: Backend

---

## O que este módulo faz

Faz o login real do advogado no e-SAJ (TJSP) usando Playwright: preenche CPF + senha, aguarda o duplo fator, captura o código de verificação automaticamente via Gmail/Outlook API, aquece a sessão e extrai os cookies autenticados. É disparado como validação em background logo depois do cadastro de credenciais (`POST /credentials/esaj`) ou manualmente (`POST /credentials/esaj/revalidar`), e persiste o resultado em `TribunalSession` para o frontend consultar via polling. Este módulo **não** agenda execuções recorrentes — isso é a Etapa 7 (APScheduler), que vai reaproveitar exatamente as mesmas funções construídas aqui.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/services/auth_esaj.py` | Motor de login Playwright: `realizar_login`, `selecionar_cookies_sessao`, `LoginEsajError` |
| `backend/app/services/email_capture.py` | Busca o código de verificação por e-mail (Gmail/Outlook): `buscar_codigo_esaj`, funções puras `eh_email_do_esaj`/`extrair_codigo_verificacao` |
| `backend/app/services/credential_validation.py` | Orquestrador: `validar_credencial_esaj` — decripta, chama o login, persiste `TribunalSession`/`JobLog` |
| `backend/app/services/oauth_gmail.py` / `oauth_outlook.py` | `refresh_access_token` (novo nesta etapa) além de `build_authorize_url`/`exchange_code` (Etapa 5) |
| `backend/app/api/credentials.py` | `POST /credentials/esaj` dispara a validação; novo `POST /credentials/esaj/revalidar`; `GET /credentials/status` agora inclui `session_status` |
| `backend/app/models/tribunal.py` | `TribunalSession` (`cookie_encrypted` agora nullable — ADR-007) |
| `backend/app/models/job_log.py` | `JobLog` — cada tentativa de login grava uma linha (`tipo="login"`) |
| `frontend/src/features/settings/EsajCredentialForm.tsx` | Polling de `session_status`, mensagens por status, botão "Revalidar" |

---

## Endpoints

| Método | Rota | Descrição | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/credentials/esaj` | Salva CPF/senha; dispara validação em background **só se o e-mail já estiver conectado** | Bearer | 5/hora por IP |
| POST | `/credentials/esaj/revalidar` | Dispara nova tentativa de login sem reenviar CPF/senha (exige e-mail conectado) | Bearer | 5/hora por IP |
| GET | `/credentials/status` | Inclui `session_status` (join com `TribunalSession`) | Bearer | — |

`session_status` é um dos `SESSION_STATUSES` (`ativo`, `reauth_pendente`, `bloqueado`, `credencial_invalida`, `email_desconectado`, `portal_indisponivel`, `codigo_nao_encontrado`) ou `None` se nenhuma validação nunca foi disparada para a credencial.

Fluxo de onboarding típico: salvar CPF/senha → conectar e-mail (callback OAuth dispara a validação automaticamente) → polling até `ativo` ou falha. Sem e-mail, o status fica `null` com aviso na UI; não inicia Playwright.

---

## Funções e hooks públicos (frontend)

| Nome | Arquivo | Descrição |
|---|---|---|
| `revalidarCredencialEsaj` | `features/settings/credentials.api.ts` | `POST /credentials/esaj/revalidar` |
| `estaValidando` / `MENSAGENS_SESSION_STATUS` | `features/settings/EsajCredentialForm.tsx` | Deriva o estado de UI (validando/sucesso/falha) e a mensagem final por `session_status` |

`EsajCredentialForm` usa `refetchInterval` do TanStack Query: 3s **somente** enquanto `session_status === "reauth_pendente"`; `null` não é tratado como “validando” (mostra aviso para conectar e-mail ou clicar em Revalidar).

---

## Arquitetura do fluxo

```
SPA                  POST /credentials/esaj      BackgroundTask         Playwright (e-SAJ)      Gmail/Outlook API
 │  cpf + senha  ────────────────────────────>│                        │                        │
 │<──── 200 (cadastrado=true, status=null) ───│  (sem e-mail: não dispara Playwright)
 │  conectar Outlook/Gmail (OAuth)  ─────────>│ callback salva token   │                        │
 │                                             │─ validar_credencial_esaj(user_id) ──────────────>│
 │                                             │      upsert TribunalSession status=reauth_pendente
 │  GET /credentials/status (poll 3s)  ───────>│                        │                        │
 │<──── session_status=reauth_pendente ────────│                        │                        │
 │                                             │───────────────────────>│ preenche CPF+senha,     │
 │                                             │                        │ submit, modal MFA       │
 │                                             │                        │───── busca e-mail (poll 3s) ──>│
 │                                             │                        │<──── código 6 dígitos ──────────│
 │                                             │                        │ preenche código, aquece │
 │                                             │                        │ tarefas-adv, extrai cookies │
 │                                             │<── cookies ────────────│                        │
 │                                             │ TribunalSession status=ativo, cookie_encrypted   │
 │                                             │ JobLog(tipo=login, status=sucesso)               │
 │  GET /credentials/status (poll seguinte) ──>│                        │                        │
 │<──── session_status=ativo ───────────────────│                        │                        │
```

O browser roda via Playwright **sync** em `asyncio.to_thread` (necessário no Windows: o event loop do uvicorn não lança subprocessos). O callback async de MFA é ponteado com `run_coroutine_threadsafe`. Toda a chamada roda sob `asyncio.wait_for(timeout=60)` no orquestrador.

---

## Padrões seguidos neste módulo

- **Decriptação só em memória:** `credential_validation.validar_credencial_esaj` decripta `cpf_encrypted`/`senha_encrypted` em variáveis locais, nunca em atributo de classe ou cache; as variáveis são descartadas (`= None`) no `finally` ao fim da função
- **Contexto Playwright isolado:** `auth_esaj.realizar_login` abre um contexto novo por chamada (`headless=True`), via API sync em thread (compatível com Windows/uvicorn), sempre fechado em `finally` — nunca reaproveitado entre advogados
- **Chromium no path estável:** se `PLAYWRIGHT_BROWSERS_PATH` apontar para cache efêmero do Cursor (`cursor-sandbox-cache`), redireciona para `%LOCALAPPDATA%\ms-playwright`
- **Erros mapeados, nunca crus:** `LoginEsajError.tipo` é sempre um dos `SESSION_STATUSES` já existentes; nenhuma mensagem de erro do Playwright, do e-SAJ ou de rede chega a `TribunalSession.ultimo_erro`/`JobLog.erro` — só o tipo
- **Screenshot só em desenvolvimento:** `_salvar_screenshot_debug` verifica `settings.is_development` antes de gravar qualquer captura de tela (que pode conter CPF preenchido) em disco
- **Callback em vez de import direto:** `auth_esaj.py` recebe `obter_codigo` como parâmetro (`Callable[[datetime], Awaitable[str]]`) em vez de importar `email_capture` — mantém o motor de login testável sem rede e sem depender do provedor de e-mail
- **Sessão dedicada na captura MFA (ADR-009):** `buscar_codigo_esaj(user_id, since)` abre `SessionLocal` própria por iteração — nunca recebe a `AsyncSession` do orquestrador. Timeout de 60s seta `asyncio.Event` para parar o polling
- **Filtro de remetente na API:** Gmail lista com `q=from:tjsp.jus.br after:{epoch}` antes do `format=full`; Outlook lista sem `body` e só então busca o corpo das mensagens que passaram em `eh_email_do_esaj`
- **Cookie só com `ativo`:** falha, `reauth_pendente` e desconexão de e-mail chamam `TribunalSession.anular_cookie()` (`cookie_encrypted`/`expires_at` nulos)
- **Refresh de token best-effort:** `email_capture._get_autenticado` tenta a chamada com o `access_token` salvo; só chama `refresh_access_token` se receber 401, e regrava `email_oauth_token_encrypted` (já criptografado) na sessão dedicada da captura
- **Guarda de concorrência em memória:** `_VALIDACOES_EM_ANDAMENTO` (processo) evita duas validações simultâneas do mesmo `user_id` — limitação conhecida e documentada na ADR-008 (não protege entre múltiplos workers)
- **`JobLog` sempre gravado:** toda tentativa (sucesso ou falha) grava uma linha `tipo="login"` com `duracao_ms` e `erro` (tipo, nunca detalhe sensível)
- **Timeout duro de 60s:** `asyncio.wait_for` no orquestrador, conforme `security.mdc` §8
- **Resposta:** `CredentialStatusSchema` ganha `session_status: str | None` — nunca expõe cookie, CPF ou senha

---

## Modelo de dados relacionado

```python
class TribunalSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tribunal_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "tribunal"),
        Index("ix_tribunal_sessions_status_proximo_retry", "status", "proximo_retry"),
    )

    user_id: Mapped[uuid.UUID]                       # FK users.id CASCADE
    tribunal: Mapped[str]                            # "esaj_tjsp"
    cookie_encrypted: Mapped[bytes | None]           # AES-256-GCM; None até 1º login bem-sucedido (ADR-007)
    expires_at: Mapped[datetime | None]              # now() + 22h no sucesso
    status: Mapped[str]                              # um dos SESSION_STATUSES
    ultimo_erro: Mapped[str | None]                  # tipo do erro, nunca detalhe
    tentativas_falha: Mapped[int]
    proximo_retry: Mapped[datetime | None]           # backoff 5→15→60min (bookkeeping; scheduler usa na Etapa 7)
    ultimo_sucesso: Mapped[datetime | None]
```

Uma linha por advogado+tribunal, criada (ou atualizada) a cada chamada de `validar_credencial_esaj`. Migration: `a46336bed1eb_torna_cookie_encrypted_nullable_em_.py`.

`JobLog` (tabela `job_logs`, já existente desde antes desta etapa) recebe uma linha `tipo="login"` por tentativa.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Credenciais do e-SAJ e Conexão de E-mail (Etapa 5) | Usa `TribunalCredential.cpf_encrypted`/`senha_encrypted`/`email_oauth_token_encrypted`, `encrypt_secret`/`decrypt_secret`, `mask_cpf` |
| Autenticação da Plataforma | `CurrentUser`/`get_current_user` nos dois endpoints novos |

Módulos futuros que vão depender deste:

| Módulo | Uso |
|---|---|
| Scheduler / cron de reautenticação (Etapa 7) | Vai chamar `validar_credencial_esaj` diretamente às 1h da manhã, reaproveitando o mesmo orquestrador |
| Pipes de coleta (intimações, audiências, petições, processos) | Vão decriptar `TribunalSession.cookie_encrypted` (quando `status == "ativo"`) para autenticar chamadas às APIs internas do e-SAJ |

---

## O que NÃO fazer aqui

- ❌ Não decriptar CPF/senha/cookie fora do escopo de `validar_credencial_esaj` — nunca em atributo de classe, cache global, ou log
- ❌ Não deixar `LoginEsajError`/exceções do Playwright ou de `email_capture` chegarem cruas a `TribunalSession.ultimo_erro` ou `JobLog.erro` — sempre mapear para um `SESSION_STATUSES`
- ❌ Não compartilhar `browser`/`context` do Playwright entre chamadas de `realizar_login` — sempre um contexto novo, sempre fechado em `finally`
- ❌ Não tirar screenshot de depuração fora de `settings.is_development`
- ❌ Não importar `email_capture` dentro de `auth_esaj.py` — a captura de código é sempre injetada via callback
- ❌ Não reaproveitar um código de e-mail anterior a `since` (o instante exato em que o MFA foi solicitado) — `email_capture` sempre filtra por data além de por remetente
- ❌ Não tratar `POST /credentials/esaj` (resposta 200) como "credencial validada" — só `session_status == "ativo"` no polling confirma o login real (ADR-008)
- ❌ Não persistir `access_token`/`refresh_token` renovados só em memória — `email_capture` sempre regrava `email_oauth_token_encrypted` criptografado na sessão dedicada da captura
- ❌ Não passar a `AsyncSession` do orquestrador para `buscar_codigo_esaj` — a thread do Playwright sobrevive ao `wait_for` (ADR-009)
- ❌ Não deixar cookie antigo no banco após falha, `reauth_pendente` ou `DELETE` de credencial/e-mail
- ❌ Não mapear `CodigoNaoEncontradoError` para `portal_indisponivel` — o status é `codigo_nao_encontrado`
- ❌ Não confiar só na query da API de e-mail para filtrar remetente/data — sempre revalidar em código (`eh_email_do_esaj`, comparação de datas)
- ❌ Não baixar o corpo do e-mail antes de filtrar remetente na API (Gmail `q=from:`, Outlook `$select` sem `body`)

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-13 | Etapa 6: motor de login Playwright (`auth_esaj.py`), captura de código por e-mail com polling e refresh de token (`email_capture.py`, `refresh_access_token` em `oauth_gmail.py`/`oauth_outlook.py`), orquestrador (`credential_validation.py`), disparo em `BackgroundTask` a partir de `POST /credentials/esaj`, novo `POST /credentials/esaj/revalidar`, `session_status` em `GET /credentials/status`, migration tornando `cookie_encrypted` nullable (ADR-007), validação em background + polling do frontend (ADR-008) |
| 2026-08-17 | Correções pós-smoke: Playwright sync em thread (Windows), Chromium fora do cache sandbox, validação só com e-mail conectado, callback OAuth dispara validação, polling só em `reauth_pendente`, limpeza do cache de credenciais no logout |
| 2026-08-17 | Hardening do code review: DELETE da `TribunalSession`, sessão SQLAlchemy dedicada na captura MFA (ADR-009), filtro de remetente na API antes do corpo, cookie anulado em falha/reauth, status `codigo_nao_encontrado` |

# Módulo: Credenciais do e-SAJ e Conexão de E-mail (OAuth2)

> Última atualização: 2026-08-17
> Camada: Backend / Frontend

---

## O que este módulo faz

Guarda, de forma criptografada, o CPF e a senha que o advogado usa para logar no e-SAJ (TJSP), e conecta a caixa de e-mail dele (Gmail ou Outlook) via OAuth2 para que, na Etapa 6, o job de login por Playwright consiga localizar o código de verificação enviado pelo e-SAJ. Este módulo **não** faz login no e-SAJ nem lê e-mail — só coleta e guarda as credenciais/tokens necessários para isso acontecer depois.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/api/credentials.py` | Endpoints `/credentials/*` (CRUD e-SAJ + OAuth2 authorize/callback) |
| `backend/app/core/security.py` | `encrypt_secret`/`decrypt_secret` (AES-256-GCM) e `create_oauth_state_token`/`decode_oauth_state_token` |
| `backend/app/core/cpf.py` | `is_valid_cpf`, `mask_cpf`, `normalize_cpf` |
| `backend/app/core/validators.py` | Regra de senha por bytes (`SENHA_MIN`/`SENHA_MAX`), compartilhada com `schemas/auth.py` |
| `backend/app/schemas/credentials.py` | `EsajCredentialCreateSchema`, `CredentialStatusSchema`, `AuthorizeUrlSchema` |
| `backend/app/services/oauth_gmail.py` | `build_authorize_url` / `exchange_code` do Gmail (httpx puro) |
| `backend/app/services/oauth_outlook.py` | `build_authorize_url` / `exchange_code` do Microsoft Graph (httpx puro) |
| `backend/app/services/oauth_common.py` | Exceção e timeout compartilhados pelos dois provedores |
| `backend/app/models/tribunal.py` | `TribunalCredential` (linha por advogado+tribunal) |
| `backend/app/db/migrations/versions/f3d81e3a40ed_*.py` | Migration de `cpf_mascarado` |
| `frontend/src/features/settings/credentials.api.ts` | Wrappers tipados dos endpoints |
| `frontend/src/features/settings/credentials.types.ts` | Contratos TS (`CredentialStatus`, `AuthorizeUrlResponse`) |
| `frontend/src/features/settings/credentials.schemas.ts` | Zod do CPF (checksum) e senha |
| `frontend/src/features/settings/credentials.constants.ts` | Chave de query do TanStack Query compartilhada pelos cards |
| `frontend/src/features/settings/EsajCredentialForm.tsx` | Form de CPF/senha + estado cadastrado/remover |
| `frontend/src/features/settings/EmailConnectionCard.tsx` | Botões conectar/desconectar Gmail/Outlook |
| `frontend/src/features/settings/SettingsPage.tsx` | Compõe os dois cards + feedback do retorno do OAuth2 |
| `frontend/src/routes/configuracoes.tsx` | Rota `/configuracoes` (`requireAuth` + `?email=conectado\|erro`) |
| `frontend/src/lib/password-validation.ts` | Regra de senha por bytes compartilhada com `features/auth` |

---

## Endpoints

| Método | Rota | Descrição | Auth | Rate limit |
|---|---|---|---|---|
| GET | `/credentials/status` | Status combinado (e-SAJ + e-mail + `session_status`) | Bearer | — |
| POST | `/credentials/esaj` | Cria ou substitui CPF+senha; valida em background só se e-mail já conectado | Bearer | 5/hora por IP |
| POST | `/credentials/esaj/revalidar` | Revalida login no e-SAJ sem reenviar CPF/senha | Bearer | 5/hora por IP |
| DELETE | `/credentials/esaj` | Remove a credencial **e** a `TribunalSession` (cookies) do mesmo tribunal | Bearer | — |
| DELETE | `/credentials/email` | Desconecta o e-mail, anula o cookie e marca `session_status=email_desconectado` | Bearer | — |
| GET | `/credentials/email/{provider}/authorize` | Gera `state` assinado e devolve a URL de consentimento | Bearer | 10/hora por IP |
| GET | `/credentials/email/{provider}/callback` | Recebe o redirect do provedor, troca `code` por token, salva criptografado e dispara validação e-SAJ | **Pública** (chamada pelo browser, sem Bearer) | — |

> `provider` é `gmail` ou `outlook`. `/callback` fica com `include_in_schema=False`: não é uma rota que o frontend chama diretamente, é o `redirect_uri` configurado no Google/Microsoft.

Resposta de status (`CredentialStatusSchema`) — nunca inclui CPF, senha ou token OAuth2 reais:

```json
{
  "cadastrado": true,
  "tribunal": "esaj_tjsp",
  "cpf_mascarado": "***.456.789-**",
  "email_provider": "gmail",
  "email_conectado": true,
  "last_validated_at": null,
  "is_active": true,
  "session_status": "ativo",
  "sessao_expirada": false
}
```

> `session_status` (adicionado na Etapa 6 — ver `/docs/modulos/login-esaj.md`) reflete o resultado da última tentativa de login real no e-SAJ; `null` até a primeira validação rodar. `sessao_expirada` é `true` só quando `session_status` ainda é `ativo` mas o cookie passou do `expires_at` (~22h) — a UI mostra Revalidar nesse caso, sem devolver o cookie.

---

## Funções e hooks públicos (frontend)

| Nome | Arquivo | Descrição |
|---|---|---|
| `buscarStatusCredenciais` / `salvarCredencialEsaj` / `removerCredencialEsaj` / `revalidarCredencialEsaj` / `desconectarEmail` / `buscarUrlDeAutorizacaoEmail` | `features/settings/credentials.api.ts` | Chamadas HTTP tipadas |
| `CREDENTIALS_STATUS_QUERY_KEY` | `features/settings/credentials.constants.ts` | Chave de cache do TanStack Query, invalidada após salvar/remover/conectar/desconectar e no retorno do OAuth2 |
| `EsajCredentialForm` / `EmailConnectionCard` | `features/settings/*.tsx` | Cards independentes, cada um busca o próprio status via `useQuery` |

Validação de formulário: `zod` + `react-hook-form` + `@hookform/resolvers` (UX apenas — o backend revalida com Pydantic, incluindo o checksum do CPF).

---

## Fluxo OAuth2 (Gmail / Outlook)

```
SPA                                    Backend                              Provedor
 │  GET /credentials/email/{p}/authorize (Bearer)                              │
 │─────────────────────────────────────>│                                     │
 │                                       │ state = JWT assinado (user_id,      │
 │                                       │ provider, nonce, exp 10min)         │
 │<──────────────── { authorize_url } ──│                                     │
 │  window.location.href = authorize_url                                      │
 │─────────────────────────────────────────────────────────────────────────>  │
 │                                       │           usuário consente          │
 │                                       │<──── GET /callback?code&state ──────│
 │                                       │ valida state → user_id              │
 │                                       │ POST token endpoint (code→tokens)   │
 │                                       │ AES-256-GCM(tokens) → DB            │
 │<──── 302 /configuracoes?email=... ───│                                     │
```

O `authorize_url` é devolvido como JSON (não um 302 direto) porque a chamada ao `/authorize` é feita com `fetch`/axios e o header `Authorization: Bearer` não sobreviveria a um redirect de navegação. É o frontend quem faz `window.location.href = authorize_url`.

O `/callback` é navegação pura do browser — nunca chega com header `Authorization`. Por isso o `state` (JWT stateless, ver ADR-006) é a única forma segura de recuperar `user_id` e `provider` nesse ponto. Qualquer falha (state ausente/expirado/adulterado, provider trocado, credencial e-SAJ removida nesse meio tempo, erro na troca do código) redireciona para `?email=erro` sem nunca expor o motivo exato na URL.

---

## Padrões seguidos neste módulo

- **Criptografia:** AES-256-GCM (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`) — `encrypt_secret`/`decrypt_secret` em `security.py`; chave derivada de `AES_KEY` via SHA-256 (`Settings.derive_aes_key()`), nunca exigindo que o `.env` tenha exatamente 32 bytes
- **Blob no banco:** `nonce (12 bytes) || ciphertext+tag`, tudo em uma coluna `BYTEA` só; nonce novo a cada chamada de `encrypt_secret`
- **CPF:** validado com checksum (`is_valid_cpf`) antes de criptografar; mascarado (`mask_cpf`) e persistido em texto puro em `cpf_mascarado` — nunca decriptamos `cpf_encrypted` só para exibir (ADR-005)
- **Token de e-mail:** payload JSON (`access_token`, `refresh_token`, `expires_in`, `token_type`) — nunca inclui `id_token` nem outros campos com dado pessoal do provedor — criptografado inteiro com `encrypt_secret` antes de salvar
- **State do OAuth2:** JWT assinado stateless (`create_oauth_state_token`/`decode_oauth_state_token`), exp de 10 min, `type="oauth_state"` — sem tabela de sessão de OAuth (ADR-006)
- **Escopo mínimo:** `gmail.readonly` (Google) e `offline_access Mail.Read` (Microsoft) — sempre somente leitura, nunca escrita/envio/exclusão
- **Rate limit:** `POST /credentials/esaj` e `POST /credentials/esaj/revalidar` a 5/hora por IP; `GET /credentials/email/{provider}/authorize` a 10/hora por IP (`app/core/rate_limit.py`)
- **Resposta:** `CredentialStatusSchema` / `AuthorizeUrlSchema` — nunca ORM, nunca CPF/senha/token reais
- **Ownership:** toda query filtra por `user_id = current_user.id` (ou pelo `user_id` decodificado do `state`, no callback) — nunca aceita `user_id` do cliente
- **Config sem segredo:** `google_client_id`/`secret`, `microsoft_client_id`/`secret` são `str = ""` por padrão; endpoints de `/authorize` respondem 503 com mensagem clara enquanto não configurados, em vez de travar o boot da aplicação

---

## Modelo de dados relacionado

```python
class TribunalCredential(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "tribunal_credentials"
    __table_args__ = (UniqueConstraint("user_id", "tribunal"),)

    user_id: Mapped[uuid.UUID]              # FK users.id CASCADE
    tribunal: Mapped[str]                   # "esaj_tjsp"
    cpf_encrypted: Mapped[bytes]            # AES-256-GCM
    senha_encrypted: Mapped[bytes]          # AES-256-GCM
    cpf_mascarado: Mapped[str]              # "***.456.789-**", texto puro (ADR-005)
    email_provider: Mapped[str | None]      # "gmail" | "outlook" | None
    email_oauth_token_encrypted: Mapped[bytes | None]  # AES-256-GCM (JSON com os tokens)
    last_validated_at: Mapped[datetime | None]  # null até a Etapa 6 rodar o 1º login real
    is_active: Mapped[bool]
```

Uma linha por advogado+tribunal (hoje só `esaj_tjsp`). Migration da coluna nova: `f3d81e3a40ed_adiciona_cpf_mascarado_em_tribunal_.py`.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Autenticação | `CurrentUser`/`get_current_user` em toda rota exceto `/callback`; `create_access_token`/`decode_access_token` inspiraram o padrão do `oauth_state` |
| Migrations / camada de dados | Tabela `tribunal_credentials`, sessão async, Alembic |

Módulos que já dependem deste (Etapa 6 — ver `/docs/modulos/login-esaj.md`):

| Módulo | Uso |
|---|---|
| Login Playwright (`auth_esaj.py`) | Decripta `cpf_encrypted`/`senha_encrypted` em memória para logar no e-SAJ |
| Captura de código por e-mail (`email_capture.py`) | Decripta `email_oauth_token_encrypted`, renova via `refresh_token` se expirado, lê e-mails do domínio do e-SAJ |

---

## O que NÃO fazer aqui

- ❌ Não devolver CPF, senha ou token OAuth2 reais em nenhum schema de resposta — só `cpf_mascarado` e booleanos de status
- ❌ Não decriptar `cpf_encrypted`/`senha_encrypted`/`email_oauth_token_encrypted` a partir de uma requisição HTTP — decriptação só acontece em memória, dentro do job (Etapa 6)
- ❌ Não guardar `id_token` do Google (carrega e-mail/nome) nem qualquer campo do token além do necessário para autenticar chamadas futuras à API de e-mail
- ❌ Não usar tabela de sessão para o `state` do OAuth2 — é stateless por design (ADR-006)
- ❌ Não aceitar um `state` vazio, expirado, com `provider` diferente do da URL do callback, ou assinado com outro `type` (ex.: um access token reaproveitado)
- ❌ Não pedir escopo de escrita/envio/exclusão do Gmail ou Outlook — só leitura
- ❌ Não logar CPF, senha, cookie ou token OAuth2 — nem em erro de decriptação (`DecriptografiaError` carrega só `"TagInvalida"`, nunca o blob)
- ❌ Não reaproveitar nonce do AES-GCM entre chamadas — `encrypt_secret` sempre gera um novo
- ❌ Não expor o motivo exato de falha do callback na URL de redirect — sempre `?email=erro` genérico
- ❌ Não apagar só `TribunalCredential` no DELETE `/esaj` — a `TribunalSession` (cookie) vai junto
- ❌ Não desconectar o e-mail deixando `session_status=ativo` — marcar `email_desconectado` e anular o cookie

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-11 | Etapa 5 (backend): `encrypt_secret`/`decrypt_secret` (AES-256-GCM), `create_oauth_state_token`/`decode_oauth_state_token`, validação/mascaramento de CPF (`app/core/cpf.py`), migration `cpf_mascarado`, CRUD de credenciais e-SAJ, serviços OAuth2 (`oauth_gmail.py`/`oauth_outlook.py`, httpx puro) e endpoints `/credentials/email/{provider}/authorize\|callback`. Extraída a regra de senha por bytes para `app/core/validators.py` (compartilhada com `schemas/auth.py`) |
| 2026-08-11 | Etapa 5 (frontend): feature `features/settings` (API, schemas Zod com checksum de CPF, `EsajCredentialForm`, `EmailConnectionCard`, `SettingsPage`), rota `/configuracoes` com `requireAuth`, link "Configurações" no `Navbar`. Extraída a regra de senha por bytes para `lib/password-validation.ts` (compartilhada com `features/auth`) |
| 2026-08-13 | Etapa 6: `CredentialStatusSchema` ganhou `session_status`; detalhes completos do login real (Playwright, captura de código por e-mail, orquestrador, `POST /credentials/esaj/revalidar`) documentados em `/docs/modulos/login-esaj.md` |
| 2026-08-17 | Callback OAuth passa a disparar validação; `POST /esaj` só valida se e-mail já conectado; endpoints de revalidar documentados na tabela |
| 2026-08-17 | Hardening: DELETE `/esaj` apaga a sessão; DELETE `/email` devolve `email_desconectado`; rate limit no `/authorize`; `POST /esaj` invalida sessão antiga |

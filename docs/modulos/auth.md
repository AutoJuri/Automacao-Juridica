# Módulo: Autenticação da Plataforma

> Última atualização: 2026-08-09
> Camada: Backend / Frontend

---

## O que este módulo faz

Autentica advogados na plataforma AdvogAtiva: cadastro, login, logout, renovação de sessão e recuperação de senha. O access token JWT vive só em memória no frontend; o refresh token opaco fica em cookie HttpOnly e é revogável no banco. A UI split-screen e as guardas de rota do painel dependem deste módulo.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/api/auth.py` | Endpoints `/auth/*` |
| `backend/app/api/deps.py` | `get_current_user` / aliases `CurrentUser`, `DbSession` |
| `backend/app/core/security.py` | bcrypt, JWT, geração/hash de tokens opacos |
| `backend/app/core/rate_limit.py` | SlowAPI + limites das rotas públicas |
| `backend/app/schemas/auth.py` | Request/Response Pydantic |
| `backend/app/models/refresh_token.py` | Tabela `refresh_tokens` |
| `backend/app/models/password_reset_token.py` | Tabela `password_reset_tokens` |
| `backend/app/db/migrations/versions/38d4177c211b_*.py` | Migration das tabelas de token |
| `frontend/src/features/auth/auth.api.ts` | Wrappers tipados dos endpoints |
| `frontend/src/features/auth/auth.types.ts` | Contratos TS (`TokenResponse`, etc.) |
| `frontend/src/features/auth/auth.schemas.ts` | Zod dos formulários |
| `frontend/src/features/auth/auth.errors.ts` | Tradução de status HTTP → mensagem UX |
| `frontend/src/features/auth/AuthShell.tsx` | Moldura split-screen reutilizável |
| `frontend/src/features/auth/LoginPage.tsx` | Toggle login / registro / esqueci senha |
| `frontend/src/features/auth/{Login,Register,ForgotPassword,ResetPassword}Form.tsx` | Formulários com RHF + zod + useMutation |
| `frontend/src/store/auth.store.ts` | Zustand: `accessToken` + `user` em memória |
| `frontend/src/lib/axios.ts` | Interceptor Bearer + refresh deduplicado |
| `frontend/src/lib/session-bootstrap.ts` | Restore silencioso no boot da SPA |
| `frontend/src/lib/route-guards.ts` | `requireAuth` / `requireGuest` para `beforeLoad` |
| `frontend/src/routes/redefinir-senha.tsx` | Rota pública `?token=` |

---

## Endpoints

| Método | Rota | Descrição | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/auth/cadastro` | Cria usuário, emite sessão | Não | 5/hora por IP |
| POST | `/auth/login` | Autentica e emite sessão | Não | 10/hora por IP |
| POST | `/auth/refresh` | Rotaciona refresh cookie → novo access | Cookie | — |
| POST | `/auth/logout` | Revoga refresh no banco e limpa cookie | Cookie (não exige Bearer) | — |
| GET | `/auth/me` | Dados públicos do usuário | Bearer | — |
| POST | `/auth/recuperar-senha` | Gera token de reset (resposta genérica) | Não | 3/hora por IP |
| POST | `/auth/redefinir-senha` | Troca senha + revoga todas as sessões | Não (token no body) | — |

> Rotas protegidas usam `Depends(get_current_user)`.
> `user_id` nunca é aceito via body ou query — sempre vem do JWT (`sub`).

Resposta de sessão (`TokenResponseSchema`):

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": { "id": "...", "name": "...", "email": "..." }
}
```

O refresh token **não** aparece no JSON — só no `Set-Cookie` (`HttpOnly`, `Secure` fora de development, `SameSite=Strict`, `Path=/auth`).

---

## Funções e hooks públicos (frontend)

| Nome | Arquivo | Descrição |
|---|---|---|
| `cadastrar` / `login` / `logout` / `recuperarSenha` / `redefinirSenha` / `buscarUsuarioAtual` | `features/auth/auth.api.ts` | Chamadas HTTP tipadas |
| `refreshAccessToken` | `lib/axios.ts` | Renova sessão; dedup de chamadas concorrentes |
| `ensureSessionRestored` | `lib/session-bootstrap.ts` | Uma tentativa de refresh por carregamento da SPA |
| `requireAuth` / `requireGuest` | `lib/route-guards.ts` | Guardas de `beforeLoad` |
| `useAuthStore` | `store/auth.store.ts` | `setAuth` / `clearAuth` / `isAuthenticated` |
| `AuthShell` | `features/auth/AuthShell.tsx` | Layout visual das telas de auth |

Validação de formulário: `zod` + `react-hook-form` + `@hookform/resolvers` (UX apenas — o backend revalida com Pydantic).

---

## Fluxo de sessão

```
Boot SPA
  └─ __root beforeLoad → ensureSessionRestored()
       └─ POST /auth/refresh (cookie) → setAuth(access, user) | clearAuth

Login / Cadastro
  └─ POST /auth/login|cadastro → setAuth + navigate /

Request protegida
  └─ Axios injeta Authorization: Bearer <access>
       └─ 401 (exceto login/cadastro/refresh)
            └─ refreshAccessToken() (promise única)
                 ├─ ok → retry da request original
                 └─ falha → clearAuth + redirect /login

Logout
  └─ POST /auth/logout → clearAuth + /login
```

---

## Padrões seguidos neste módulo

- **Senha:** bcrypt 12 rounds; rejeita senha > 72 bytes (limite do bcrypt)
- **JWT:** payload mínimo (`sub`, `type`, `iat`, `exp`); vida curta (~15 min)
- **Refresh:** token opaco aleatório; no banco só o SHA-256 (`token_hash`); rotação a cada `/auth/refresh` via `UPDATE ... WHERE revoked_at IS NULL RETURNING` atômico (evita duas requisições concorrentes emitirem duas sessões do mesmo cookie); reuso de um token já revogado revoga todas as sessões ativas do usuário
- **Cookie:** `HttpOnly` + `SameSite=Strict` + `Secure` (exceto development) + `Path=/auth`
- **Access no cliente:** só Zustand em memória — nunca `localStorage` / `sessionStorage`
- **Resposta:** `UserPublicSchema` / `TokenResponseSchema` / `MessageSchema` — nunca ORM
- **Enumeração de e-mails:** login e recuperar-senha devolvem mensagens que não revelam se o e-mail existe; o login também equaliza o **tempo** de resposta com `verify_password_or_dummy` (roda bcrypt mesmo sem usuário) — ver `docs/backlog-auth-hardening.md` para o mesmo ajuste em `recuperar-senha`
- **Reset de senha:** invalida tokens anteriores do usuário; ao redefinir, revoga **todos** os refresh tokens ativos
- **Rate limit:** SlowAPI por IP, storage em memória (uma instância); ver ADR-003 para o envio do link
- **Segredos:** fora de `development`, `Settings` rejeita `JWT_SECRET`/`AES_KEY` placeholder e exige `JWT_SECRET` ≥ 32 chars
- **Guardas de rota:** TanStack Router `beforeLoad` — só UX; a API continua sendo a fonte de verdade
- **Refresh concorrente:** uma única `Promise` compartilhada — necessário porque o backend rotaciona o cookie

---

## Modelo de dados relacionado

```
users
├── refresh_tokens          (migration 38d4177c211b)
└── password_reset_tokens   (migration 38d4177c211b)
```

```python
class RefreshToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[uuid.UUID]  # FK users.id CASCADE
    token_hash: Mapped[str]     # SHA-256, unique
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]

class PasswordResetToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "password_reset_tokens"
    user_id: Mapped[uuid.UUID]  # FK users.id CASCADE
    token_hash: Mapped[str]     # SHA-256, unique
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
```

`users.password_hash` é preenchido via `hash_password` no cadastro/redefinição. O schema público **nunca** inclui `password_hash`.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Migrations / camada de dados | Tabela `users`, sessão async, Alembic |

Módulos futuros que vão depender deste:

| Módulo | Uso |
|---|---|
| Qualquer rota protegida | `CurrentUser` / `get_current_user` |
| `credentials` | Ownership do advogado autenticado |
| `processos` / painel | Guardas de rota + Bearer nas APIs |

---

## O que NÃO fazer aqui

- ❌ Não salvar access token (nem refresh) em `localStorage` / `sessionStorage` — risco de XSS
- ❌ Não devolver o refresh token no JSON — só no cookie HttpOnly
- ❌ Não persistir o token bruto de refresh/reset no banco — só o hash SHA-256
- ❌ Não logar senha, access token, refresh token ou password_hash
- ❌ Não revelar se um e-mail está cadastrado (login 401 genérico; recuperar-senha sempre a mesma mensagem)
- ❌ Não limpar o cookie em branches que levantam `HTTPException` no `/auth/refresh` — o exception handler descarta a Response original
- ❌ Não disparar refresh no interceptor para `/auth/login`, `/auth/cadastro` ou `/auth/refresh` — loop infinito
- ❌ Não usar dois mecanismos de guarda (componente `ProtectedRoute` + `beforeLoad`) — só `route-guards.ts`
- ❌ Não confiar só na expiração do JWT no logout — sempre revogar o refresh no banco
- ❌ Não aceitar `user_id` do cliente — sempre do `sub` do access token
- ❌ Não enviar e-mail real ainda — ver ADR-003 (link no log do servidor)

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-09 | Etapa 3 (backend): endpoints de auth, bcrypt, JWT, refresh em cookie, rate limit, recuperação de senha, migration `38d4177c211b` |
| 2026-08-09 | Etapa 4 (frontend): formulários reais (zod + RHF), interceptor com refresh deduplicado, bootstrap de sessão, guardas `requireAuth`/`requireGuest`, telas esqueci/redefinir senha, `AuthShell`; log do backend passa a emitir URL completa do reset |
| 2026-08-09 | Correções do code review (itens 1–6): `clearAuth` após redefinir senha; log do link de reset restrito a `development` (ADR-003); `--proxy-headers` no Dockerfile para o rate limit ver o IP real por trás do proxy do Railway; rotação do refresh e uso do token de reset via `UPDATE ... RETURNING` atômico (fecha corrida de duas requisições concorrentes) + detecção de reuso de refresh (revoga todas as sessões do usuário); `verify_password_or_dummy` no login para equalizar o tempo de resposta entre e-mail existente/inexistente; validação de senha por bytes UTF-8 (não só caracteres) no Pydantic e no Zod. Achados 7+ documentados em `docs/backlog-auth-hardening.md` |

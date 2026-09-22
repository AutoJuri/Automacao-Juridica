# PRD — Automação Jurídica
> Documento vivo — atualizar conforme o projeto evolui.
> Versão 0.2 | Status: Em desenvolvimento

---

## 1. Resumo do Produto

**Automação Jurídica** é uma plataforma web que automatiza o monitoramento de processos judiciais para advogados autônomos e pequenos escritórios. O sistema acessa os portais dos tribunais (inicialmente e-SAJ/TJSP) usando as credenciais do próprio advogado, coleta atualizações dos processos de forma automática e notifica o usuário dentro do app quando há novas movimentações. Futuramente, também gerará templates de resposta com auxílio de IA.

**Público-alvo inicial:** Advogados autônomos e pequenos escritórios jurídicos.

---

## 2. Problema e Objetivo

### Problema
Advogados perdem tempo considerável acessando manualmente portais de tribunais (como o e-SAJ) todos os dias para verificar se houve atualização nos processos de seus clientes. Esse processo é repetitivo, manual e propenso a erros de acompanhamento.

### Objetivo
Eliminar o trabalho manual de monitoramento processual, entregando ao advogado um painel centralizado onde ele visualiza todos os seus processos e recebe alertas automáticos quando há novas movimentações — sem precisar acessar o portal do tribunal.

### Resultado esperado (sucesso)
- Advogado não precisa mais entrar no e-SAJ diariamente para checar processos
- Todas as atualizações são consolidadas em um único lugar
- Redução significativa do tempo gasto em tarefas operacionais de acompanhamento

---

## 3. Escopo

### MVP (primeira entrega)
- Cadastro e login do advogado na plataforma
- Cadastro das credenciais do advogado no e-SAJ (armazenamento seguro com AES-256)
- Conexão OAuth2 com Gmail ou Outlook para captura automática do código de verificação
- Login automatizado no e-SAJ via Playwright (CPF + senha + código do email)
- Importação automática de todos os processos vinculados ao advogado no e-SAJ
- Monitoramento periódico automático a cada 10 minutos via PIPES (intimações, audiências, petições, processos)
- Reautenticação automática diária às 1h da manhã para renovar o cookie de sessão
- Complemento de dados via API pública do DataJud (CNJ)
- Painel web listando todos os processos e seus status
- Notificação in-app quando há nova movimentação em algum processo
- Visualização do histórico de movimentações de cada processo

### Fora do escopo (não fazer agora)
- App mobile
- App desktop / certificado digital A3
- Suporte a outros tribunais além do e-SAJ (PJe, eProc, PROJUDI)
- Notificações por e-mail ou WhatsApp
- Geração de templates de resposta com IA (abordagem **decidida** no ADR-016; código ainda não existe)
- Modelo de monetização / pagamentos
- Multi-usuário / gestão de equipe dentro do escritório
- Integração com softwares jurídicos de terceiros (ADVBox, Astrea, etc.)
- Download e armazenamento de PDFs da pasta digital
- Migração de APScheduler para Celery

### Futuro (pós-MVP)
- Suporte a outros sistemas judiciais (PJe, eProc, PROJUDI, TRFs)
- Notificações por e-mail e WhatsApp
- Geração de templates / minuta com IA (copiloto da elaboração: sugestão de peça, estilo do modelo, fatos extras, chat/grifo, anexos; jurisprudência só o que o advogado marcar — ADR-016)
- App mobile (iOS e Android)
- App desktop com suporte a certificado digital A3 via PKCS#11
- Modelo de monetização (assinatura mensal ou cobrança por processo — a definir)
- Dashboard com métricas e relatórios para o escritório
- Migração do orquestrador para Celery + Redis conforme escala
- Download e visualização de PDFs da pasta digital

---

## 4. Personas, Jornadas e Fluxos

### Persona principal
**João, advogado autônomo**
- Atua em vara cível, tem entre 30 e 80 processos ativos simultâneos
- Acessa o e-SAJ diariamente para checar novidades, processo por processo
- Usa computador (Windows/Mac) no escritório
- Não tem equipe — faz tudo sozinho
- Dor principal: tempo gasto em tarefas repetitivas que poderiam ser automatizadas

### Caminho feliz (fluxo crítico do MVP)

```
1. João acessa a plataforma e cria sua conta (e-mail + senha)
2. João entra em "Configurações" e cadastra suas credenciais do e-SAJ (CPF + senha)
3. João conecta sua conta de email (Gmail ou Outlook) via OAuth2
4. O sistema faz login automatizado no e-SAJ com Playwright:
   → Preenche CPF + senha
   → e-SAJ envia código para o email de João
   → Sistema captura o código via Gmail/Outlook API automaticamente
   → Completa o login e salva o cookie de sessão (válido ~24h)
5. O sistema importa automaticamente todos os processos da carteira de João
6. João vê o painel com todos os seus processos listados
7. A cada 10 minutos, os PIPES rodam e verificam atualizações usando o cookie salvo
8. Às 1h da manhã, o sistema renova o cookie automaticamente (novo login)
9. Quando há nova movimentação, João recebe notificação in-app
10. João clica na notificação e vê o detalhe da movimentação do processo
```

---

## 5. Funcionalidades (Priorizada)

### P0 — Essencial para o MVP funcionar

- **[AUTH]** Cadastro de conta com e-mail e senha
- **[AUTH]** Login / logout com JWT (access token + refresh token)
- **[CREDENTIALS]** Cadastro seguro das credenciais do e-SAJ (AES-256)
- **[CREDENTIALS]** Conexão OAuth2 com Gmail e Outlook para captura do código
- **[CREDENTIALS]** Validação das credenciais (teste de login ao salvar)
- **[SCRAPING]** Login automatizado no e-SAJ via Playwright + captura de código por email
- **[SCRAPING]** Reautenticação diária às 1h da manhã por advogado
- **[SCRAPING]** PIPE A — coleta de intimações a cada 10 min
- **[SCRAPING]** PIPE B — coleta de audiências a cada 10 min
- **[SCRAPING]** PIPE C — coleta de petições a cada 10 min
- **[SCRAPING]** PIPE D — coleta e atualização de processos a cada 10 min
- **[SCRAPING]** ETL — transformação e normalização dos dados coletados
- **[SCRAPING]** Lógica de diff — compara novo dado com o salvo, notifica se diferente
- **[DATAJUD]** Complemento de dados via API pública do DataJud (CNJ)
- **[PROCESSOS]** Painel com listagem de todos os processos (número, status, última atualização)
- **[PROCESSOS]** Tela de detalhe do processo com histórico de movimentações
- **[NOTIFICAÇÃO]** Notificação in-app quando há nova movimentação

### P1 — Importante, mas não bloqueia o MVP

- **[PROCESSOS]** Filtros e busca na listagem (por número, status, data)
- **[PROCESSOS]** Indicador visual de processos com atualizações não lidas
- **[SCRAPING]** Re-sincronização manual (botão "Atualizar agora")
- **[AUTH]** Recuperação de senha por e-mail
- **[RESILIÊNCIA]** Tratamento de cookie expirado com reautenticação automática imediata
- **[RESILIÊNCIA]** Backoff exponencial em caso de rate limiting do e-SAJ

### P2 — Desejável, entra se houver tempo

- **[PROCESSOS]** Ordenação da listagem por diferentes critérios
- **[UX]** Onboarding guiado para novos usuários
- **[UX]** Estado vazio com instrução clara quando não há processos ainda
- **[OBS]** Dashboard interno de saúde dos jobs (quantos rodaram, falharam, etc.)

---

## 6. Requisitos e Regras de Negócio

### Fluxo de autenticação no e-SAJ

```
Advogado cadastra CPF + senha + conecta email (OAuth2)
                    ↓
Sistema executa Playwright:
  1. Acessa esaj.tjsp.jus.br
  2. Preenche CPF e senha
  3. e-SAJ envia código para o email do advogado
  4. Gmail API / Microsoft Graph API captura o código automaticamente
  5. Playwright digita o código
  6. Sistema extrai e salva o cookie (JSESSIONID + CASTGC) criptografado no banco
                    ↓
Cookie válido por ~24h → pipes usam o cookie salvo
                    ↓
Às 1h da manhã → scheduler renova o cookie para cada advogado
```

### Ciclo de coleta (PIPES)

```
A cada 10 minutos, para cada advogado ativo:
  1. Verifica se o cookie está válido (expires_at - 2h de margem)
  2. Se inválido → agenda reautenticação imediata → pula esse ciclo
  3. Se válido → executa os 4 pipes em paralelo:
     PIPE A: GET /tarefas-adv/api/intimacoes
     PIPE B: GET /tarefas-adv/api/audiencias
     PIPE C: GET /tarefas-adv/api/peticoes
     PIPE D: GET /tarefas-adv/api/processos?cdsProcesso=...
  4. ETL transforma os dados brutos → formato interno
  5. Diff compara com o que está salvo no banco
  6. Se há diferença → salva nova versão + gera notificação in-app
  7. Se igual → descarta silenciosamente
```

### Tratamento de erros por tipo

| Tipo de erro | Resposta do sistema |
|---|---|
| 401/403 — cookie expirado | Reautentica imediatamente, retoma na próxima janela |
| 429 — rate limiting | Backoff exponencial: 5min → 15min → 60min → pula o ciclo |
| 5xx / timeout — portal fora do ar | Loga, pula todos os advogados, retoma no próximo ciclo |
| Credencial inválida (senha trocada) | Para tentativas, notifica advogado para atualizar credenciais |
| Email OAuth2 expirado | Notifica advogado para reconectar o email |

### Regra do cookie

```python
# Salva com margem de segurança de 2h
expires_at = datetime.now() + timedelta(hours=22)  # cookie dura ~24h

# Antes de cada pipe, verifica
if cookie.expires_at < datetime.now():
    trigger_reauth(advogado_id)
    return
```

### Notificações in-app
- Badge/contador no ícone de notificações
- Lista de notificações com data/hora e descrição da movimentação
- Marcar como lida ao clicar
- Marcar todas como lidas
- Apenas notifica quando há diferença real — nunca duplica

### Status do advogado (campo na tabela `tribunal_sessions`)

| Status | Significado |
|---|---|
| `ativo` | Cookie válido, pipes rodando normalmente |
| `reauth_pendente` | Cookie expirou, reautenticação em andamento |
| `bloqueado` | Rate limit ativo, aguardando backoff |
| `credencial_invalida` | Advogado trocou senha no e-SAJ, ação necessária |
| `email_desconectado` | OAuth2 do email expirou, reconexão necessária |
| `portal_indisponivel` | e-SAJ fora do ar, aguardando normalização |

---

## 7. Critérios de Aceite

| Funcionalidade | Critério |
|---|---|
| Cadastro | Usuário cria conta e acessa o app em menos de 2 minutos |
| Credenciais e-SAJ | Sistema valida, salva criptografado e inicia importação automaticamente |
| Conexão de email | Advogado conecta Gmail ou Outlook via OAuth2 em menos de 1 minuto |
| Login automatizado | Sistema completa login no e-SAJ (CPF + senha + código) sem intervenção humana |
| Importação | Todos os processos do advogado aparecem no painel após importação inicial |
| Monitoramento | Nova movimentação gera notificação in-app em até 1 ciclo de 10 minutos |
| Renovação de cookie | Sistema renova o cookie às 1h sem intervenção do advogado |
| Notificação | Exibe número do processo e descrição da movimentação |
| Detalhe do processo | Histórico completo de movimentações em ordem cronológica |
| Erro de credencial | Sistema exibe mensagem clara e para tentativas até o advogado atualizar |
| Resiliência | Falha em 1 advogado não impacta coleta dos demais |

---

## 8. Stack Técnica e Arquitetura

### Frontend
- **Framework:** React com TypeScript
- **Estilo:** Tailwind CSS
- **Componentes UI:** shadcn/ui
- **Roteamento:** TanStack Router
- **Requisições/Cache:** TanStack Query + Axios
- **Estado global:** Zustand
- **Plataforma:** Web (responsivo, desktop-first)

### Backend
- **Linguagem:** Python 3.12
- **Gerenciador de pacotes:** UV (substitui pip + virtualenv + pip-tools — equivalente ao Bun para Python)
- **Framework:** FastAPI
- **Servidor ASGI:** Uvicorn
- **Autenticação:** JWT (access token curto ~15min + refresh token ~7 dias via cookie HttpOnly)
- **Orquestrador de jobs:** APScheduler (roda dentro do FastAPI — migrar para Celery conforme escala)
- **Scraping / automação:** Playwright (login no e-SAJ) + httpx (chamadas às APIs internas)
- **Parsing HTML:** BeautifulSoup4 + lxml (para páginas sem API JSON, ex: detalhes do processo)

### Integrações de terceiros
- **Gmail API** (Google Cloud) — captura automática do código de verificação do e-SAJ
- **Microsoft Graph API** (Azure Portal) — idem para usuários Outlook/Hotmail
- **DataJud API** (CNJ) — complemento de dados processuais, gratuito, cobre todos os tribunais
- **e-SAJ (TJSP)** — via Playwright para login + httpx para APIs internas descobertas:
  - `GET /tarefas-adv/api/intimacoes`
  - `GET /tarefas-adv/api/audiencias`
  - `GET /tarefas-adv/api/peticoes`
  - `GET /tarefas-adv/api/processos?cdsProcesso=...`
  - `GET /cpopg/show.do?processo.codigo=...` (HTML — BeautifulSoup)
  - `GET /pastadigital/getPDF.do?...` (PDF — futuro)

### Infra/Deploy
- **Plataforma:** Railway (frontend + backend + banco na mesma plataforma)
- **Repositório:** Monorepo simples — `frontend/` e `backend/` no mesmo repositório Git, sem ferramenta de orquestração (Turborepo não se aplica — stack híbrida JS + Python)
- **Containerização:** Dockerfile — garante ambiente idêntico entre dev e prod, e resolve dependências de sistema do Playwright (Chromium) no Railway
- **Ambientes:** dev (local via Docker) → prod (Railway via Dockerfile)
- **Variáveis de ambiente:** gerenciadas pelo Railway (nunca hardcoded)
- **Banco de dados:** PostgreSQL via Railway (plugin nativo)
- **Staging:** fora do escopo do MVP

### Estrutura do Monorepo

```
automacao-juridica/
├── frontend/                        # React + TypeScript + Bun
│   ├── package.json
│   ├── bun.lockb
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── assets/
│       ├── components/
│       │   └── ui/                  # componentes shadcn/ui
│       ├── features/
│       │   ├── auth/                # login, registro, recuperação de senha
│       │   └── processos/           # painel, detalhe, notificações
│       ├── hooks/
│       ├── lib/
│       │   ├── axios.ts             # instância configurada do axios
│       │   └── utils.ts             # cn() e utilitários
│       ├── pages/
│       ├── routes/                  # TanStack Router
│       ├── store/                   # Zustand stores
│       └── types/                   # types e interfaces globais
│
├── backend/                         # FastAPI + Python + UV
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── .env.example
│   └── app/
│       ├── main.py                  # entrypoint FastAPI + APScheduler
│       ├── api/
│       │   ├── auth.py              # rotas de autenticação
│       │   ├── processos.py         # rotas de processos
│       │   ├── credentials.py       # rotas de credenciais e OAuth2
│       │   └── notifications.py     # rotas de notificações
│       ├── services/
│       │   ├── auth_esaj.py         # login automatizado (Playwright)
│       │   ├── email_capture.py     # Gmail API + Microsoft Graph API
│       │   ├── datajud.py           # integração DataJud CNJ
│       │   └── pipes/
│       │       ├── pipe_intimacoes.py
│       │       ├── pipe_audiencias.py
│       │       ├── pipe_peticoes.py
│       │       └── pipe_processos.py
│       ├── etl/
│       │   ├── etl.py               # transformação e normalização
│       │   └── diff.py              # comparação e geração de notificações
│       ├── models/                  # SQLAlchemy models
│       ├── schemas/                 # Pydantic schemas (request/response)
│       ├── core/
│       │   ├── security.py          # JWT, bcrypt, AES-256
│       │   ├── scheduler.py         # APScheduler — jobs e horários
│       │   └── config.py            # variáveis de ambiente
│       └── db/
│           ├── session.py           # conexão async PostgreSQL
│           └── migrations/          # Alembic migrations
│
├── .gitignore
└── README.md

---

## 9. Banco de Dados

**Banco:** PostgreSQL via Railway  
**ORM:** SQLAlchemy 2.0 (async) + Alembic (migrations)

### Entidades e campos

**users**
```
id              UUID PK
email           VARCHAR UNIQUE NOT NULL
password_hash   VARCHAR NOT NULL          -- bcrypt, mínimo 12 rounds
name            VARCHAR NOT NULL
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
```

**tribunal_credentials**
```
id              UUID PK
user_id         UUID FK → users
tribunal        VARCHAR NOT NULL          -- ex: "esaj_tjsp"
cpf_encrypted   BYTEA NOT NULL            -- AES-256
senha_encrypted BYTEA NOT NULL            -- AES-256
email_provider  VARCHAR                   -- "gmail" | "outlook"
email_oauth_token_encrypted  BYTEA        -- token OAuth2 do email, AES-256
last_validated_at  TIMESTAMP WITH TIME ZONE
is_active       BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP WITH TIME ZONE
```

**tribunal_sessions**
```
id              UUID PK
user_id         UUID FK → users
tribunal        VARCHAR NOT NULL
cookie_encrypted  BYTEA NOT NULL          -- JSESSIONID + CASTGC, AES-256
expires_at      TIMESTAMP WITH TIME ZONE  -- now() + 22h (margem de segurança)
status          VARCHAR NOT NULL          -- ativo | reauth_pendente | bloqueado | credencial_invalida | email_desconectado | portal_indisponivel
ultimo_erro     TEXT
tentativas_falha  INTEGER DEFAULT 0
proximo_retry   TIMESTAMP WITH TIME ZONE
ultimo_sucesso  TIMESTAMP WITH TIME ZONE
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
```

**processos**
```
id              UUID PK
user_id         UUID FK → users
tribunal        VARCHAR NOT NULL
cd_processo     VARCHAR NOT NULL          -- código interno do e-SAJ
nu_processo     VARCHAR                   -- número CNJ formatado
de_classe       VARCHAR                   -- classe processual
de_assunto      VARCHAR                   -- assunto
instancia       VARCHAR                   -- PG, SG, etc.
parte_ativa     JSONB                     -- {nome, nomeSocial, representada}
parte_passiva   JSONB                     -- {nome, representada}
url_cpo         VARCHAR                   -- link para página do processo
url_pasta       VARCHAR                   -- link para pasta digital
status          VARCHAR
last_synced_at  TIMESTAMP WITH TIME ZONE
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE

UNIQUE (user_id, cd_processo)
```

**movimentacoes**
```
id              UUID PK
processo_id     UUID FK → processos
data_movimentacao  TIMESTAMP WITH TIME ZONE
descricao       TEXT NOT NULL
titulo          VARCHAR                   -- ex: "Outras Decisões"
instancia       VARCHAR
is_new          BOOLEAN DEFAULT TRUE      -- flag para notificação
created_at      TIMESTAMP WITH TIME ZONE

UNIQUE (processo_id, data_movimentacao, descricao)  -- evita duplicatas
```

**intimacoes**
```
id              UUID PK
user_id         UUID FK → users
processo_id     UUID FK → processos (nullable)
id_esaj         VARCHAR UNIQUE NOT NULL   -- id composto vindo da API do e-SAJ
titulo          VARCHAR
descricao       TEXT
instancia       VARCHAR
data_movimentacao  TIMESTAMP WITH TIME ZONE
ciencia         BOOLEAN DEFAULT FALSE     -- se o advogado já deu ciência no e-SAJ
is_new          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP WITH TIME ZONE
```

**audiencias**
```
id              UUID PK
user_id         UUID FK → users
processo_id     UUID FK → processos (nullable)
id_esaj         VARCHAR UNIQUE NOT NULL
titulo          VARCHAR
data_audiencia  TIMESTAMP WITH TIME ZONE
local           VARCHAR
is_new          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP WITH TIME ZONE
```

**notifications**
```
id              UUID PK
user_id         UUID FK → users
processo_id     UUID FK → processos (nullable)
tipo            VARCHAR NOT NULL          -- "movimentacao" | "intimacao" | "audiencia" | "sistema"
titulo          VARCHAR NOT NULL
message         TEXT NOT NULL
is_read         BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP WITH TIME ZONE
```

**job_logs**
```
id              UUID PK
user_id         UUID FK → users (nullable — logs de sistema não têm user)
tipo            VARCHAR NOT NULL          -- "login" | "pipe_intimacoes" | "pipe_audiencias" | "pipe_peticoes" | "pipe_processos" | "reauth"
status          VARCHAR NOT NULL          -- "sucesso" | "falha" | "skip"
erro            TEXT                      -- detalhes do erro se houver
duracao_ms      INTEGER
created_at      TIMESTAMP WITH TIME ZONE
```

### Relacionamentos

```
users 1→N tribunal_credentials
users 1→N tribunal_sessions
users 1→N processos
users 1→N notifications
processos 1→N movimentacoes
processos 1→N intimacoes
processos 1→N audiencias
```

### Estrutura do Dockerfile (backend)

```dockerfile
FROM python:3.12-slim

# UV — gerenciador de pacotes
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependências de sistema do Playwright (Chromium)
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python via UV (lockfile garante reprodutibilidade)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. Arquitetura de Scraping

> A estrutura de pastas completa está na seção 8 (Monorepo).

### Scheduler — jobs e horários

```python
# Roda às 1h da manhã — renova cookies de todos os advogados ativos
scheduler.add_job(renovar_todos_cookies, 'cron', hour=1, minute=0)

# Roda a cada 10 minutos — executa pipes de todos os advogados ativos
scheduler.add_job(executar_todos_pipes, 'interval', minutes=10)
```

### Fluxo do ETL

```
Dado bruto da API do e-SAJ (JSON)
        ↓
ETL normaliza → formato interno padrão
        ↓
Diff compara com banco:
  → hash do conteúdo atual vs hash do novo dado
  → se igual: descarta
  → se diferente: salva nova versão + cria notification
```

---

## 11. UX/UI e Identidade Visual

- **Objetivo de estilo:** Light theme com navbar dark — painel principal limpo e branco, sidebar clara, header escuro como âncora visual. Profissional e denso em informação, adequado ao contexto jurídico.
- **Tom:** Confiança, controle, eficiência operacional
- **Componentes base:** shadcn/ui
- **O que evitar:** Dark theme total, design excessivamente colorido, gamificação

### Tema Geral
Light theme com navbar dark — a seção principal é clara/branca, apenas o header superior é escuro.

### Paleta de Cores

| Token | Hex | Uso |
|---|---|---|
| `bg-navbar` | `#0D0F14` | Header/navbar superior (único elemento dark) |
| `bg-base` | `#F0F2F7` | Background geral da aplicação (off-white) |
| `bg-sidebar` | `#F5F6FA` | Sidebar esquerda |
| `bg-surface` | `#FFFFFF` | Cards, painéis, painel principal |
| `bg-surface-hover` | `#F8F9FC` | Hover em cards |
| `border-subtle` | `#E5E7EB` | Bordas sutis dos cards e divisores |
| `border-active` | `#C7D0E8` | Borda de card ativo/selecionado |
| `text-primary` | `#111827` | Texto principal (dark sobre fundo claro) |
| `text-muted` | `#6B7280` | Labels, textos secundários, metadados |
| `text-navbar` | `#FFFFFF` | Texto dentro da navbar dark |
| `accent-blue` | `#3B5BDB` | Badge TJSP, links, ações primárias |
| `accent-orange` | `#F97316` | Badge TRF3 e outros tribunais |
| `accent-purple` | `#8B5CF6` | Tags de tipo processual |
| `accent-amber` | `#F59E0B` | Prazo médio, botões de ação secundária |
| `status-critical` | `#EF4444` | Prazo crítico, alertas urgentes |
| `status-online` | `#22C55E` | Indicador de serviço ativo/online |

### Layout e Estrutura
- **Sidebar lateral esquerda:** Lista de processos em acompanhamento (fixados pelo advogado)
- **Painel principal:** Detalhe do processo selecionado
- **Header fixo:** Nome do produto + status do serviço
- Cards de processo: tribunal (badge colorido), número, cliente, prazo, última movimentação
- Detalhe do processo: etapas judiciais em timeline + gabinete de documentos lado a lado

---

## 12. Qualidade, Segurança e Operação

### Segurança
- Credenciais do e-SAJ (CPF, senha, cookie, token OAuth2) armazenadas com AES-256 via `cryptography` lib — chave em variável de ambiente (`ENCRYPTION_KEY`), nunca no código
- Senhas da plataforma hasheadas com bcrypt (mínimo 12 rounds)
- JWT: access token de 15 minutos em memória (Zustand), refresh token de 7 dias em cookie HttpOnly + Secure
- `user_id` sempre extraído do token JWT no backend — nunca aceito do body/query
- Rate limiting nas rotas de autenticação
- Schemas de resposta Pydantic explícitos — nunca retornar model ORM diretamente
- Validação de ownership: `resource.user_id == current_user.id` antes de qualquer retorno
- Logs nunca contêm credenciais, cookies ou tokens
- HTTPS obrigatório em produção
- Variáveis sensíveis apenas em variáveis de ambiente do Railway

### Requisitos não-funcionais
- Listagem de processos carrega em menos de 2 segundos
- Falha em 1 advogado não impacta coleta dos demais
- Jobs de scraping com timeout máximo de 60 segundos por advogado

### Observabilidade (tabela `job_logs`)
- Log de cada execução de pipe: tipo, status, duração, erro
- Log de cada login/reautenticação
- Alerta interno se taxa de falha > 20% dos advogados em um ciclo

### Estratégia de testes
- **Unitários:** funções de ETL/diff, parsing HTML (BeautifulSoup), criptografia
- **Integração:** fluxo de autenticação JWT, rotas protegidas, ownership
- **E2E:** fluxo crítico completo (cadastro → credenciais → login e-SAJ → ver processos → notificação)

---

## 13. Decisões em Aberto

| Decisão | Opções | Prazo para decidir |
|---|---|---|
| Modelo de monetização | Assinatura mensal, por processo, freemium | Pré-lançamento |
| Tipografia | DM Sans + DM Serif Display ou outra | Antes de implementar o frontend |
| Migração Celery | Quando o APScheduler não aguentar a carga | Conforme escala |

### Decisões já tomadas

| Decisão | Escolha |
|---|---|
| Banco de dados | PostgreSQL (Railway plugin) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Framework backend | FastAPI + Uvicorn |
| Gerenciador de pacotes Python | UV |
| Containerização | Dockerfile (deploy no Railway + Playwright no prod) |
| Estrutura do repositório | Monorepo simples (frontend/ + backend/ no mesmo repo Git) |
| Orquestrador de jobs (MVP) | APScheduler (dentro do FastAPI) |
| Criptografia de credenciais | AES-256 via `cryptography` lib |
| Captura de código e-SAJ | Gmail API (Google) + Microsoft Graph API (Outlook) |
| Scraping login | Playwright (login) + httpx (APIs internas) |
| Parsing HTML | BeautifulSoup4 + lxml |
| Complemento de dados | DataJud API pública (CNJ) — gratuito |
| Deploy / infra | Railway (backend + banco + frontend) |
| Design system | Light theme com navbar dark — paleta definida na seção 11 |
| Frequência de sincronização | A cada 10 minutos (pipes) + renovação às 1h (login) |

---

*Última atualização: julho/2026*

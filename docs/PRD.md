# PRD — Automação Jurídica
> Documento vivo — atualizar conforme o projeto evolui.
> Versão 0.3 | Status: Em desenvolvimento

---

## 1. Resumo do Produto

**Automação Jurídica** é uma plataforma web que automatiza o monitoramento de processos judiciais para advogados autônomos e escritórios jurídicos. O sistema acessa os portais dos tribunais (inicialmente e-SAJ/TJSP) usando as credenciais do próprio advogado, coleta atualizações dos processos de forma automática e notifica o usuário quando há novas movimentações. A plataforma também suporta **organizações** — escritórios com múltiplos membros, papéis hierárquicos e gestão colaborativa de processos e tarefas via **Kanban**.

**Público-alvo:** Advogados autônomos e escritórios jurídicos de pequeno e médio porte.

---

## 2. Problema e Objetivo

### Problema
Advogados perdem tempo considerável acessando manualmente portais de tribunais todos os dias para verificar atualizações em processos. Em escritórios com equipe, o problema se multiplica: não há visibilidade centralizada, delegação de tarefas é feita por WhatsApp ou planilha, e o controle de prazos depende de memória individual.

### Objetivo
Eliminar o trabalho manual de monitoramento processual e centralizar a gestão operacional do escritório em uma única plataforma — com monitoramento automatizado, notificações em tempo real e gestão de tarefas colaborativa.

### Resultado esperado (sucesso)
- Advogado não precisa mais entrar no e-SAJ diariamente para checar processos
- Escritórios conseguem gerenciar processos e tarefas da equipe em um único lugar
- Redução significativa do tempo gasto em tarefas operacionais de acompanhamento
- Owner e Admin têm visibilidade total do escritório sem depender de relatórios manuais

---

## 3. Escopo

### MVP (primeira entrega)
- Cadastro e login individual na plataforma
- Criação e gestão de organizações (escritórios)
- Convite e gestão de membros com 4 papéis hierárquicos (Owner, Admin, Advogado, Assistente)
- Cadastro de credenciais do e-SAJ por usuário individual ou compartilhadas na organização (AES-256)
- Conexão OAuth2 com Gmail ou Outlook para captura automática do código de verificação
- Login automatizado no e-SAJ via Playwright (CPF + senha + código do email)
- Importação automática de todos os processos vinculados ao advogado no e-SAJ
- Monitoramento periódico automático a cada 10 minutos via PIPES (intimações, audiências, petições, processos)
- Reautenticação automática diária às 1h da manhã para renovar o cookie de sessão
- Complemento de dados via API pública do DataJud (CNJ)
- Visibilidade de processos por papel: Owner/Admin veem tudo, Advogado/Assistente só os seus
- Painel web de processos com listagem e detalhe de movimentações
- Notificação in-app quando há nova movimentação
- Kanban de tasks com colunas configuráveis
- Tasks independentes ou vinculadas a processos
- Atribuição de tasks entre membros da organização

### Fora do escopo (não fazer agora)
- App mobile
- App desktop / certificado digital A3
- Suporte a outros tribunais além do e-SAJ (PJe, eProc, PROJUDI)
- Notificações por e-mail ou WhatsApp
- Geração de templates de resposta com IA
- Modelo de monetização / pagamentos
- Integração com softwares jurídicos de terceiros (ADVBox, Astrea, etc.)
- Download e armazenamento de PDFs da pasta digital
- Migração de APScheduler para Celery
- Relatórios e dashboards gerenciais por organização
- Comentários e threads dentro de tasks

### Futuro (pós-MVP)
- Suporte a outros sistemas judiciais (PJe, eProc, PROJUDI, TRFs) via JUDIT API
- Notificações por e-mail e WhatsApp
- Geração de templates / minuta com IA (copiloto de elaboração de peças)
- App mobile (iOS e Android)
- App desktop com suporte a certificado digital A3 via PKCS#11
- Modelo de monetização (assinatura por organização ou por usuário — a definir)
- Dashboard gerencial por organização (processos, prazos, produtividade da equipe)
- Comentários e threads em tasks
- Relatórios de produtividade por membro
- Migração do orquestrador para Celery + Redis conforme escala
- Download e visualização de PDFs da pasta digital

---

## 4. Personas, Jornadas e Fluxos

### Personas

**João, advogado autônomo**
- Atua em vara cível, tem entre 30 e 80 processos ativos simultâneos
- Usa a plataforma sozinho, sem organização
- Dor principal: tempo gasto em monitoramento manual no e-SAJ

**Marina, sócia-fundadora do escritório**
- Gerencia 5 advogados e 2 assistentes
- Precisa de visibilidade total dos processos e tarefas da equipe
- Cria a organização, convida membros, define papéis
- Papel: **Owner**

**Carlos, advogado sênior do escritório**
- Responsável por uma carteira de processos dentro do escritório
- Pode gerenciar tasks da equipe, mas não mexe em configurações da organização
- Papel: **Admin**

**Ana, advogada júnior**
- Executa tarefas delegadas, acompanha seus próprios processos
- Não vê processos de outros membros, só os seus
- Papel: **Advogado**

**Pedro, assistente jurídico**
- Apoia os advogados com tasks operacionais
- Acesso mais restrito — só vê e executa o que foi atribuído a ele
- Papel: **Assistente**

### Caminho feliz — Advogado autônomo

```
1. João cria conta com e-mail + senha
2. João cadastra credenciais do e-SAJ (CPF + senha) + conecta Gmail/Outlook
3. Sistema faz login automatizado no e-SAJ e importa todos os processos
4. João vê painel com todos os processos listados
5. A cada 10min, pipes verificam atualizações automaticamente
6. João recebe notificação in-app quando há nova movimentação
7. João cria tasks para si mesmo no Kanban
```

### Caminho feliz — Escritório com equipe

```
1. Marina cria conta e cria uma organização ("Escritório Silva & Associados")
2. Marina convida Carlos (Admin), Ana (Advogado) e Pedro (Assistente) por e-mail
3. Cada membro aceita o convite e entra com suas próprias credenciais da plataforma
4. Ana cadastra suas credenciais do e-SAJ (credenciais individuais)
5. Marina cadastra credenciais compartilhadas do e-SAJ do escritório (opcional)
6. Sistema importa processos de cada membro com suas credenciais
7. Marina e Carlos veem todos os processos da organização no painel
8. Ana e Pedro veem apenas os processos vinculados a elas
9. Carlos cria uma task "Protocolar petição" vinculada ao processo X e atribui para Ana
10. Ana vê a task no Kanban, move para "Em andamento" e depois para "Concluído"
11. Carlos recebe notificação de que a task foi concluída
```

---

## 5. Papéis e Permissões

### Hierarquia de papéis

| Papel | Descrição |
|---|---|
| **Owner** | Criador da organização. Acesso total e irrestrito. Único que pode excluir a organização ou transferir ownership. |
| **Admin** | Gerente operacional. Pode gerenciar membros (exceto Owner), ver todos os processos, criar e atribuir tasks. Não pode excluir a organização. |
| **Advogado** | Membro padrão. Vê e gerencia apenas seus próprios processos. Pode criar e atribuir tasks para qualquer membro. |
| **Assistente** | Membro operacional. Acesso mais restrito — vê apenas os processos e tasks atribuídos a ele. Pode criar tasks. |

### Matriz de permissões

| Ação | Owner | Admin | Advogado | Assistente |
|---|---|---|---|---|
| Criar organização | ✅ | ❌ | ❌ | ❌ |
| Excluir organização | ✅ | ❌ | ❌ | ❌ |
| Transferir ownership | ✅ | ❌ | ❌ | ❌ |
| Convidar membros | ✅ | ✅ | ❌ | ❌ |
| Remover membros | ✅ | ✅ (exceto Owner) | ❌ | ❌ |
| Alterar papel de membro | ✅ | ✅ (exceto Owner) | ❌ | ❌ |
| Ver todos os processos da org | ✅ | ✅ | ❌ | ❌ |
| Ver apenas processos próprios | ✅ | ✅ | ✅ | ✅ |
| Cadastrar credenciais e-SAJ (próprias) | ✅ | ✅ | ✅ | ❌ |
| Cadastrar credenciais e-SAJ (org compartilhada) | ✅ | ✅ | ❌ | ❌ |
| Criar task | ✅ | ✅ | ✅ | ✅ |
| Atribuir task para qualquer membro | ✅ | ✅ | ✅ | ✅ |
| Mover task no Kanban (própria ou atribuída) | ✅ | ✅ | ✅ | ✅ |
| Mover task no Kanban (qualquer) | ✅ | ✅ | ❌ | ❌ |
| Excluir task | ✅ | ✅ | ✅ (própria) | ✅ (própria) |
| Configurações da organização | ✅ | ✅ | ❌ | ❌ |

---

## 6. Funcionalidades (Priorizada)

### P0 — Essencial para o MVP funcionar

**Auth e Usuários**
- **[AUTH]** Cadastro de conta com e-mail e senha
- **[AUTH]** Login / logout com JWT (access token + refresh token)
- **[AUTH]** Recuperação de senha por e-mail

**Organizações**
- **[ORG]** Criar organização com nome e slug único
- **[ORG]** Convidar membros por e-mail com papel definido
- **[ORG]** Aceitar/recusar convite de organização
- **[ORG]** Alterar papel de membro (Owner e Admin)
- **[ORG]** Remover membro da organização
- **[ORG]** Um usuário pode pertencer a múltiplas organizações
- **[ORG]** Contexto de organização ativo (troca de org no header)

**Credenciais e e-SAJ**
- **[CREDENTIALS]** Cadastro de credenciais individuais do e-SAJ (AES-256)
- **[CREDENTIALS]** Cadastro de credenciais compartilhadas da organização (AES-256 — só Owner/Admin)
- **[CREDENTIALS]** Conexão OAuth2 com Gmail e Outlook para captura do código
- **[CREDENTIALS]** Validação das credenciais (teste de login ao salvar)

**Scraping**
- **[SCRAPING]** Login automatizado no e-SAJ via Playwright + captura de código por email
- **[SCRAPING]** Reautenticação diária às 1h da manhã por credencial ativa
- **[SCRAPING]** PIPE A — coleta de intimações a cada 10 min
- **[SCRAPING]** PIPE B — coleta de audiências a cada 10 min
- **[SCRAPING]** PIPE C — coleta de petições a cada 10 min
- **[SCRAPING]** PIPE D — coleta e atualização de processos a cada 10 min
- **[SCRAPING]** ETL — transformação e normalização dos dados coletados
- **[SCRAPING]** Lógica de diff — compara novo dado com o salvo, notifica se diferente
- **[DATAJUD]** Complemento de dados via API pública do DataJud (CNJ)

**Processos**
- **[PROCESSOS]** Painel com listagem de processos (respeitando visibilidade por papel)
- **[PROCESSOS]** Tela de detalhe com histórico de movimentações
- **[NOTIFICAÇÃO]** Notificação in-app quando há nova movimentação

**Tasks / Kanban**
- **[TASKS]** Board Kanban com colunas padrão: A Fazer, Em Andamento, Concluído
- **[TASKS]** Criar task com título, descrição, prazo e responsável
- **[TASKS]** Vincular task a um processo (opcional)
- **[TASKS]** Atribuir task para qualquer membro da organização
- **[TASKS]** Mover task entre colunas (drag and drop)
- **[TASKS]** Notificação in-app ao ser atribuído a uma task
- **[TASKS]** Notificação in-app ao task atribuída ser concluída (para o criador)

### P1 — Importante, mas não bloqueia o MVP

- **[PROCESSOS]** Filtros e busca na listagem (por número, status, data, responsável)
- **[PROCESSOS]** Indicador visual de processos com atualizações não lidas
- **[SCRAPING]** Re-sincronização manual (botão "Atualizar agora")
- **[RESILIÊNCIA]** Tratamento de cookie expirado com reautenticação automática imediata
- **[RESILIÊNCIA]** Backoff exponencial em caso de rate limiting do e-SAJ
- **[TASKS]** Filtros no Kanban (por responsável, por processo vinculado, por prazo)
- **[TASKS]** Prazo vencido com destaque visual na task
- **[ORG]** Página de membros da organização com papéis listados

### P2 — Desejável, entra se houver tempo

- **[PROCESSOS]** Ordenação da listagem por diferentes critérios
- **[UX]** Onboarding guiado para novos usuários e criação de organização
- **[UX]** Estado vazio com instrução clara quando não há processos ou tasks
- **[OBS]** Dashboard interno de saúde dos jobs
- **[TASKS]** Colunas do Kanban customizáveis por organização
- **[TASKS]** Prioridade da task (baixa, média, alta, urgente)

---

## 7. Requisitos e Regras de Negócio

### Organizações

**Criação:**
- Qualquer usuário autenticado pode criar uma organização
- Ao criar, o usuário automaticamente se torna Owner
- Slug da organização é único no sistema (ex: `silva-associados`)
- Um usuário pode ser membro de múltiplas organizações simultaneamente

**Convites:**
- Owner e Admin enviam convite por e-mail com papel definido
- Convite tem validade de 7 dias — após isso, expira e precisa ser reenviado
- Se o e-mail não tiver conta na plataforma: link para criar conta + aceitar convite
- Se já tiver conta: notificação in-app + e-mail com link de aceite
- Convite pendente pode ser cancelado por Owner ou Admin antes do aceite

**Troca de contexto:**
- Header da plataforma exibe a organização ativa com seletor de troca
- Contexto de organização determina: processos visíveis, Kanban exibido, membros disponíveis

### Credenciais do e-SAJ — modelo híbrido

```
Credenciais individuais (user_id preenchido, organization_id null):
  → Qualquer papel com permissão pode cadastrar as próprias
  → Processos importados ficam vinculados ao user_id

Credenciais compartilhadas da organização (organization_id preenchido, user_id null):
  → Só Owner e Admin podem cadastrar
  → Processos importados ficam vinculados ao organization_id
  → Visibilidade dos processos segue a matriz de papéis da org
```

### Visibilidade de processos por papel

```
Owner / Admin:
  → Todos os processos vinculados a qualquer user_id da organização
  → Todos os processos vinculados ao organization_id (credenciais compartilhadas)

Advogado / Assistente:
  → Apenas processos vinculados ao próprio user_id
  → Não veem processos de outros membros nem da org compartilhada

Usuário autônomo (sem organização):
  → Apenas seus próprios processos (user_id)
```

### Fluxo de autenticação no e-SAJ

```
Usuário cadastra CPF + senha + conecta email (OAuth2)
                    ↓
Sistema executa Playwright por credencial:
  1. Acessa esaj.tjsp.jus.br
  2. Preenche CPF e senha
  3. e-SAJ envia código para o email do usuário
  4. Gmail API / Microsoft Graph API captura o código automaticamente
  5. Playwright digita o código
  6. Sistema extrai e salva o cookie (JSESSIONID + CASTGC) criptografado no banco
                    ↓
Cookie válido por ~24h → pipes usam o cookie salvo
                    ↓
Às 1h da manhã → scheduler renova o cookie para cada credencial ativa
```

### Ciclo de coleta (PIPES)

```
A cada 10 minutos, para cada credencial ativa:
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

### Regras de Tasks

- Task sempre tem: título (obrigatório), responsável (obrigatório), coluna (obrigatório)
- Task pode ter: descrição, prazo, processo vinculado — todos opcionais
- Task de usuário autônomo (sem org): existe no contexto pessoal, organization_id null
- Task vinculada a processo: herda visibilidade do processo (quem não vê o processo não vê a task)
- Ao mover para "Concluído": notifica o criador (se diferente do responsável)
- Ao ser atribuído: notifica o responsável imediatamente
- Prazo vencido: flag `is_overdue = true`, destaque visual no card do Kanban
- Job diário às 0h30 atualiza `is_overdue` em todas as tasks com `due_date < now()` e `completed_at = null`

### Tratamento de erros por tipo (scraping)

| Tipo de erro | Resposta do sistema |
|---|---|
| 401/403 — cookie expirado | Reautentica imediatamente, retoma na próxima janela |
| 429 — rate limiting | Backoff exponencial: 5min → 15min → 60min → pula o ciclo |
| 5xx / timeout — portal fora do ar | Loga, pula todas as credenciais, retoma no próximo ciclo |
| Credencial inválida (senha trocada) | Para tentativas, notifica usuário para atualizar credenciais |
| Email OAuth2 expirado | Notifica usuário para reconectar o email |

### Status da credencial (tabela `tribunal_sessions`)

| Status | Significado |
|---|---|
| `ativo` | Cookie válido, pipes rodando normalmente |
| `reauth_pendente` | Cookie expirou, reautenticação em andamento |
| `bloqueado` | Rate limit ativo, aguardando backoff |
| `credencial_invalida` | Usuário trocou senha no e-SAJ — ação necessária |
| `email_desconectado` | OAuth2 do email expirou — reconexão necessária |
| `portal_indisponivel` | e-SAJ fora do ar, aguardando normalização |

---

## 8. Stack Técnica e Arquitetura

### Frontend
- **Framework:** React com TypeScript
- **Estilo:** Tailwind CSS
- **Componentes UI:** shadcn/ui
- **Roteamento:** TanStack Router
- **Requisições/Cache:** TanStack Query + Axios
- **Estado global:** Zustand (auth + organização ativa em memória)
- **Drag and drop (Kanban):** a definir — dnd-kit ou @hello-pangea/dnd
- **Plataforma:** Web (responsivo, desktop-first)
- **Gerenciador de pacotes:** Bun

### Backend
- **Linguagem:** Python 3.12
- **Gerenciador de pacotes:** UV
- **Framework:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.0 async + Alembic (migrations)
- **Autenticação:** JWT (access token 15min em memória + refresh token 7 dias em cookie HttpOnly)
- **Orquestrador de jobs:** APScheduler (dentro do FastAPI)
- **Scraping / automação:** Playwright (login e-SAJ) + httpx (APIs internas)
- **Parsing HTML:** BeautifulSoup4 + lxml
- **Criptografia:** AES-256 via `cryptography` lib
- **Permissões:** módulo `core/permissions.py` centraliza toda a lógica de papéis

### Integrações de terceiros
- **Gmail API** (Google Cloud) — captura automática do código de verificação do e-SAJ
- **Microsoft Graph API** (Azure Portal) — idem para usuários Outlook/Hotmail
- **DataJud API** (CNJ) — complemento de dados processuais, gratuito, 91 tribunais
- **e-SAJ (TJSP)** — Playwright para login + httpx para APIs internas:
  - `GET /tarefas-adv/api/intimacoes`
  - `GET /tarefas-adv/api/audiencias`
  - `GET /tarefas-adv/api/peticoes`
  - `GET /tarefas-adv/api/processos?cdsProcesso=...`
  - `GET /cpopg/show.do?processo.codigo=...` (HTML — BeautifulSoup)

### Infra/Deploy
- **Repositório:** Monorepo simples (`frontend/` + `backend/` no mesmo repositório Git)
- **Plataforma:** Railway (frontend + backend + banco)
- **Containerização:** Dockerfile no `backend/` (resolve dependências do Playwright/Chromium)
- **Ambientes:** dev (local) → prod (Railway)
- **Variáveis de ambiente:** gerenciadas pelo Railway (nunca hardcoded)
- **Banco de dados:** PostgreSQL via Railway (plugin nativo)

### Estrutura do Monorepo

```
automacao-juridica/
├── frontend/                          → React + Bun
│   └── src/
│       ├── features/
│       │   ├── auth/
│       │   ├── organizations/         → criação, membros, convites, troca de contexto
│       │   ├── processos/
│       │   ├── tasks/                 → Kanban, criação, atribuição
│       │   ├── notificacoes/
│       │   └── settings/
│       ├── store/                     → Zustand (auth + org ativa)
│       └── routes/                    → TanStack Router
│
├── backend/                           → FastAPI + UV
│   ├── Dockerfile
│   └── app/
│       ├── api/
│       │   ├── auth.py
│       │   ├── organizations.py       → CRUD org, membros, convites
│       │   ├── processos.py
│       │   ├── tasks.py               → CRUD tasks, Kanban
│       │   ├── credentials.py
│       │   └── notifications.py
│       ├── services/
│       │   ├── auth_esaj.py
│       │   ├── email_capture.py
│       │   ├── datajud.py
│       │   └── pipes/
│       ├── models/
│       ├── schemas/
│       ├── core/
│       │   ├── security.py            → JWT, bcrypt, AES-256
│       │   ├── permissions.py         → lógica centralizada de papéis e permissões
│       │   └── scheduler.py
│       └── db/
│           └── migrations/
│
└── docs/
    ├── INDEX.md
    ├── modulos/
    └── decisions/
```

### Estrutura do Dockerfile (backend)

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

RUN useradd -m appuser
USER appuser

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. Banco de Dados

**Banco:** PostgreSQL via Railway
**ORM:** SQLAlchemy 2.0 async + Alembic

### Entidades e campos

**users**
```
id                  UUID PK
email               VARCHAR UNIQUE NOT NULL
password_hash       VARCHAR NOT NULL          -- bcrypt 12 rounds
name                VARCHAR NOT NULL
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
```

**organizations**
```
id                  UUID PK
name                VARCHAR NOT NULL
slug                VARCHAR UNIQUE NOT NULL   -- ex: "silva-associados"
created_by          UUID FK → users
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
```

**organization_members**
```
id                  UUID PK
organization_id     UUID FK → organizations
user_id             UUID FK → users
role                VARCHAR NOT NULL          -- "owner" | "admin" | "advogado" | "assistente"
invited_by          UUID FK → users
joined_at           TIMESTAMP WITH TIME ZONE
created_at          TIMESTAMP WITH TIME ZONE

UNIQUE (organization_id, user_id)
```

**organization_invites**
```
id                  UUID PK
organization_id     UUID FK → organizations
email               VARCHAR NOT NULL          -- email do convidado
role                VARCHAR NOT NULL          -- papel que será atribuído ao aceitar
invited_by          UUID FK → users
token               VARCHAR UNIQUE NOT NULL   -- UUID do link de convite
expires_at          TIMESTAMP WITH TIME ZONE  -- validade de 7 dias
accepted_at         TIMESTAMP WITH TIME ZONE  -- null se pendente
created_at          TIMESTAMP WITH TIME ZONE
```

**tribunal_credentials**
```
id                  UUID PK
user_id             UUID FK → users (nullable — null se credencial da org)
organization_id     UUID FK → organizations (nullable — null se individual)
tribunal            VARCHAR NOT NULL           -- "esaj_tjsp"
cpf_encrypted       BYTEA NOT NULL             -- AES-256
senha_encrypted     BYTEA NOT NULL             -- AES-256
email_provider      VARCHAR                    -- "gmail" | "outlook"
email_oauth_token_encrypted  BYTEA             -- AES-256
last_validated_at   TIMESTAMP WITH TIME ZONE
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP WITH TIME ZONE

CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
```

**tribunal_sessions**
```
id                  UUID PK
credential_id       UUID FK → tribunal_credentials
cookie_encrypted    BYTEA NOT NULL             -- JSESSIONID + CASTGC, AES-256
expires_at          TIMESTAMP WITH TIME ZONE   -- now() + 22h
status              VARCHAR NOT NULL           -- ver seção 7
ultimo_erro         TEXT
tentativas_falha    INTEGER DEFAULT 0
proximo_retry       TIMESTAMP WITH TIME ZONE
ultimo_sucesso      TIMESTAMP WITH TIME ZONE
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
```

**processos**
```
id                  UUID PK
user_id             UUID FK → users (nullable — null se da org)
organization_id     UUID FK → organizations (nullable — null se individual)
tribunal            VARCHAR NOT NULL
cd_processo         VARCHAR NOT NULL
nu_processo         VARCHAR
de_classe           VARCHAR
de_assunto          VARCHAR
instancia           VARCHAR
parte_ativa         JSONB
parte_passiva       JSONB
url_cpo             VARCHAR
url_pasta           VARCHAR
status              VARCHAR
last_synced_at      TIMESTAMP WITH TIME ZONE
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE

UNIQUE (cd_processo, user_id, organization_id)
CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
```

**movimentacoes**
```
id                  UUID PK
processo_id         UUID FK → processos
data_movimentacao   TIMESTAMP WITH TIME ZONE
descricao           TEXT NOT NULL
titulo              VARCHAR
instancia           VARCHAR
is_new              BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP WITH TIME ZONE

UNIQUE (processo_id, data_movimentacao, descricao)
```

**intimacoes**
```
id                  UUID PK
user_id             UUID FK → users
organization_id     UUID FK → organizations (nullable)
processo_id         UUID FK → processos (nullable)
id_esaj             VARCHAR UNIQUE NOT NULL
titulo              VARCHAR
descricao           TEXT
instancia           VARCHAR
data_movimentacao   TIMESTAMP WITH TIME ZONE
ciencia             BOOLEAN DEFAULT FALSE
is_new              BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP WITH TIME ZONE
```

**audiencias**
```
id                  UUID PK
user_id             UUID FK → users
organization_id     UUID FK → organizations (nullable)
processo_id         UUID FK → processos (nullable)
id_esaj             VARCHAR UNIQUE NOT NULL
titulo              VARCHAR
data_audiencia      TIMESTAMP WITH TIME ZONE
local               VARCHAR
is_new              BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP WITH TIME ZONE
```

**tasks**
```
id                  UUID PK
organization_id     UUID FK → organizations (nullable — null se task pessoal)
created_by          UUID FK → users NOT NULL
processo_id         UUID FK → processos (nullable)
assigned_to         UUID FK → users (nullable)
title               VARCHAR NOT NULL
description         TEXT
column              VARCHAR NOT NULL            -- "todo" | "in_progress" | "done"
priority            VARCHAR DEFAULT 'medium'    -- "low" | "medium" | "high" | "urgent" (P2)
due_date            TIMESTAMP WITH TIME ZONE
is_overdue          BOOLEAN DEFAULT FALSE
completed_at        TIMESTAMP WITH TIME ZONE
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
```

**notifications**
```
id                  UUID PK
user_id             UUID FK → users
organization_id     UUID FK → organizations (nullable)
processo_id         UUID FK → processos (nullable)
task_id             UUID FK → tasks (nullable)
tipo                VARCHAR NOT NULL            -- "movimentacao" | "intimacao" | "audiencia" | "task_atribuida" | "task_concluida" | "convite_org" | "sistema"
titulo              VARCHAR NOT NULL
message             TEXT NOT NULL
is_read             BOOLEAN DEFAULT FALSE
created_at          TIMESTAMP WITH TIME ZONE
```

**job_logs**
```
id                  UUID PK
credential_id       UUID FK → tribunal_credentials (nullable)
tipo                VARCHAR NOT NULL            -- "login" | "pipe_intimacoes" | "pipe_audiencias" | "pipe_peticoes" | "pipe_processos" | "reauth"
status              VARCHAR NOT NULL            -- "sucesso" | "falha" | "skip"
erro                TEXT
duracao_ms          INTEGER
created_at          TIMESTAMP WITH TIME ZONE
```

### Relacionamentos

```
users 1→N organization_members
organizations 1→N organization_members
organizations 1→N organization_invites
users 1→N tribunal_credentials (individuais)
organizations 1→N tribunal_credentials (compartilhadas)
tribunal_credentials 1→1 tribunal_sessions
users 1→N processos (individuais)
organizations 1→N processos (da org)
processos 1→N movimentacoes
processos 1→N intimacoes
processos 1→N audiencias
users 1→N tasks (created_by)
users 1→N tasks (assigned_to)
organizations 1→N tasks
processos 1→N tasks
users 1→N notifications
```

---

## 10. Arquitetura de Scraping

### Scheduler — jobs e horários

```python
# Roda às 1h — renova cookies de todas as credenciais ativas
scheduler.add_job(renovar_todos_cookies, 'cron', hour=1, minute=0)

# Roda a cada 10 minutos — executa pipes de todas as credenciais ativas
scheduler.add_job(executar_todos_pipes, 'interval', minutes=10)

# Roda às 0h30 — atualiza flag is_overdue nas tasks vencidas
scheduler.add_job(atualizar_tasks_vencidas, 'cron', hour=0, minute=30)
```

### Fluxo do ETL

```
Dado bruto da API do e-SAJ (JSON)
        ↓
ETL normaliza → formato interno padrão
        ↓
Diff compara com banco (hash do conteúdo):
  → se igual: descarta
  → se diferente: salva nova versão
        ↓
Notificação gerada respeitando contexto:
  → credencial individual → notifica o user_id dono
  → credencial da org → notifica Owner + Admin + user vinculado ao processo
```

---

## 11. UX/UI e Identidade Visual

- **Objetivo de estilo:** Light theme com navbar dark — painel principal limpo e branco, sidebar clara, header escuro como âncora visual. Profissional e denso em informação.
- **Tom:** Confiança, controle, eficiência operacional
- **Componentes base:** shadcn/ui
- **O que evitar:** Dark theme total, design excessivamente colorido, gamificação

### Paleta de Cores

| Token | Hex | Uso |
|---|---|---|
| `bg-navbar` | `#0D0F14` | Header/navbar superior |
| `bg-base` | `#F0F2F7` | Background geral (off-white) |
| `bg-sidebar` | `#F5F6FA` | Sidebar esquerda |
| `bg-surface` | `#FFFFFF` | Cards, painéis, painel principal |
| `bg-surface-hover` | `#F8F9FC` | Hover em cards |
| `border-subtle` | `#E5E7EB` | Bordas sutis |
| `border-active` | `#C7D0E8` | Borda de card ativo/selecionado |
| `text-primary` | `#111827` | Texto principal |
| `text-muted` | `#6B7280` | Labels e textos secundários |
| `text-navbar` | `#FFFFFF` | Texto dentro da navbar dark |
| `accent-blue` | `#3B5BDB` | Badge TJSP, links, ações primárias |
| `accent-orange` | `#F97316` | Badge TRF3 e outros tribunais |
| `accent-purple` | `#8B5CF6` | Tags de tipo processual |
| `accent-amber` | `#F59E0B` | Prazo médio, ações secundárias |
| `status-critical` | `#EF4444` | Prazo crítico, alertas, task vencida |
| `status-online` | `#22C55E` | Indicador de serviço ativo |

### Layout e Estrutura
- **Navbar:** Nome do produto + seletor de organização ativa + notificações + perfil
- **Sidebar lateral:** Navegação principal (Processos, Kanban, Membros, Configurações)
- **Painel principal:** Conteúdo da seção ativa
- **Kanban:** Board com colunas em scroll horizontal, cards com drag and drop

---

## 12. Qualidade, Segurança e Operação

### Segurança
- Credenciais do e-SAJ, cookies e tokens OAuth2 armazenados com AES-256 — chave em `ENCRYPTION_KEY`
- Senhas hasheadas com bcrypt (mínimo 12 rounds)
- JWT: access token 15min em memória (Zustand), refresh token 7 dias em cookie HttpOnly + Secure
- `user_id` sempre extraído do JWT — nunca aceito do body/query
- Toda lógica de papel e permissão centralizada em `core/permissions.py`
- Visibilidade de processos e tasks validada no banco (WHERE clause) — nunca filtrada em Python
- Token de convite é UUID único, expira em 7 dias e é invalidado após uso
- Logs nunca contêm credenciais, cookies ou tokens
- CORS restrito à origem do frontend em produção
- HTTPS obrigatório em produção

### Requisitos não-funcionais
- Listagem de processos carrega em menos de 2 segundos
- Board Kanban carrega em menos de 1 segundo
- Falha em 1 credencial não impacta coleta das demais
- Jobs de scraping com timeout máximo de 60 segundos por credencial

### Observabilidade
- Log de cada execução de pipe: tipo, status, duração, erro (tabela `job_logs`)
- Log de cada login/reautenticação
- Alerta interno se taxa de falha > 20% das credenciais em um ciclo

### Estratégia de testes
- **Unitários:** ETL/diff, parsing HTML, criptografia, lógica de permissões por papel
- **Integração:** autenticação JWT, rotas protegidas, ownership, visibilidade por papel
- **E2E:** fluxo crítico (cadastro → org → credenciais → login e-SAJ → processos → task → notificação)

---

## 13. Decisões em Aberto

| Decisão | Opções | Prazo para decidir |
|---|---|---|
| Modelo de monetização | Por organização, por usuário, freemium | Pré-lançamento |
| Tipografia | DM Sans + DM Serif Display ou outra | Antes do frontend |
| Lib de drag and drop (Kanban) | dnd-kit vs @hello-pangea/dnd | Antes de implementar tasks |
| Migração Celery | Quando APScheduler não aguentar | Conforme escala |
| Colunas Kanban customizáveis | MVP com fixas ou já customizável | Antes de implementar tasks (P2) |

### Decisões já tomadas

| Decisão | Escolha |
|---|---|
| Banco de dados | PostgreSQL (Railway plugin) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Framework backend | FastAPI + Uvicorn |
| Gerenciador de pacotes Python | UV |
| Gerenciador de pacotes frontend | Bun |
| Containerização | Dockerfile (Railway + Playwright) |
| Estrutura do repositório | Monorepo simples (frontend/ + backend/) |
| Orquestrador de jobs (MVP) | APScheduler (dentro do FastAPI) |
| Criptografia de credenciais | AES-256 via `cryptography` lib |
| Captura de código e-SAJ | Gmail API + Microsoft Graph API (Outlook) |
| Scraping login | Playwright (login) + httpx (APIs internas) |
| Parsing HTML | BeautifulSoup4 + lxml |
| Complemento de dados | DataJud API pública (CNJ) — gratuito |
| Deploy / infra | Railway (backend + banco + frontend) |
| Design system | Light theme com navbar dark — paleta definida na seção 11 |
| Frequência de sincronização | A cada 10 minutos (pipes) + renovação às 1h (login) |
| Papéis da organização | 4 níveis: Owner, Admin, Advogado, Assistente |
| Credenciais e-SAJ | Modelo híbrido: individuais + compartilhadas por organização |
| Visibilidade de processos | Owner/Admin veem tudo — Advogado/Assistente só os seus |
| Tasks | Independentes ou vinculadas a processo, ambos os modelos |
| Atribuição de tasks | Qualquer membro pode criar e atribuir para qualquer outro |

---

*Última atualização: julho/2026*

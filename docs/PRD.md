# PRD — Automação Jurídica
> Documento vivo — atualizar conforme o projeto evolui.
> Versão 0.1 | Status: Rascunho inicial

---

## 1. Resumo do Produto

**Automação Jurídica** é uma plataforma web que automatiza o monitoramento de processos judiciais para advogados autônomos e pequenos escritórios. O sistema acessa os portais dos tribunais (inicialmente e-SAJ) usando as credenciais do próprio advogado, coleta atualizações dos processos de forma automática e notifica o usuário dentro do app quando há novas movimentações. Futuramente, também gerará templates de resposta com auxílio de IA.

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
- Cadastro das credenciais do advogado no e-SAJ (armazenamento seguro)
- Importação automática de todos os processos vinculados ao advogado no e-SAJ
- Monitoramento periódico automático dos processos (verificação de novas movimentações)
- Painel web listando todos os processos e seus status
- Notificação dentro do app quando há nova movimentação em algum processo
- Visualização do histórico de movimentações de cada processo

### Fora do escopo (não fazer agora)
- App mobile
- App desktop
- Suporte a outros tribunais além do e-SAJ
- Notificações por e-mail ou WhatsApp
- Geração de templates de resposta com IA
- Modelo de monetização / pagamentos
- Multi-usuário / gestão de equipe dentro do escritório
- Integração com softwares jurídicos de terceiros (ADVBox, Astrea, etc.)

### Futuro (pós-MVP)
- Suporte a outros sistemas judiciais (PJe, eProc, PROJUDI)
- Notificações por e-mail e WhatsApp
- Geração de templates de resposta com IA baseada nas movimentações do processo
- App mobile (iOS e Android)
- App desktop
- Modelo de monetização (assinatura mensal ou cobrança por processo monitorado — a definir)
- Dashboard com métricas e relatórios para o escritório

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
2. João entra em "Configurações" e cadastra suas credenciais do e-SAJ
3. O sistema faz login no e-SAJ com as credenciais de João
4. O sistema importa automaticamente todos os processos da carteira de João
5. João vê o painel com todos os seus processos listados
6. O sistema roda verificações periódicas (ex: a cada X horas) em background
7. Quando há nova movimentação, João recebe uma notificação dentro do app
8. João clica na notificação e vê o detalhe da movimentação do processo
```

---

## 5. Funcionalidades (Priorizada)

### P0 — Essencial para o MVP funcionar

- **[AUTH]** Cadastro de conta com e-mail e senha
- **[AUTH]** Login / logout
- **[CREDENTIALS]** Cadastro seguro das credenciais do e-SAJ do advogado
- **[CREDENTIALS]** Validação das credenciais (testar login no e-SAJ ao salvar)
- **[SCRAPING]** Importação automática dos processos vinculados ao advogado no e-SAJ
- **[SCRAPING]** Job periódico de verificação de novas movimentações
- **[PROCESSOS]** Painel com listagem de todos os processos (número, status, última atualização)
- **[PROCESSOS]** Tela de detalhe do processo com histórico de movimentações
- **[NOTIFICAÇÃO]** Notificação in-app quando há nova movimentação

### P1 — Importante, mas não bloqueia o MVP

- **[PROCESSOS]** Filtros e busca na listagem de processos (por número, status, data)
- **[PROCESSOS]** Indicador visual de processos com atualizações não lidas
- **[SCRAPING]** Re-sincronização manual pelo usuário (botão "Atualizar agora")
- **[AUTH]** Recuperação de senha por e-mail

### P2 — Desejável, entra se houver tempo

- **[PROCESSOS]** Ordenação da listagem por diferentes critérios
- **[UX]** Onboarding guiado para novos usuários (tour pelo app)
- **[UX]** Estado vazio com instrução clara quando não há processos ainda

---

## 6. Requisitos e Regras de Negócio

### Fluxos principais

**Cadastro de credenciais do e-SAJ:**
- O advogado informa usuário e senha do e-SAJ
- O sistema testa as credenciais imediatamente antes de salvar
- Se inválidas: exibe erro claro e não salva
- Se válidas: armazena de forma criptografada e dispara a importação inicial

**Importação de processos:**
- Ao salvar credenciais válidas, importação inicial roda automaticamente
- Importa todos os processos ativos da carteira do advogado no e-SAJ
- Cada processo importado fica vinculado ao advogado no banco de dados
- Progresso da importação é visível para o usuário (loading / feedback)

**Monitoramento periódico:**
- Job automático roda em background em intervalos definidos (ex: a cada 6 horas — ajustável)
- Compara movimentações novas com as já armazenadas
- Se há diferença: registra a nova movimentação e gera notificação para o advogado
- Falhas no job devem ser logadas e não devem derrubar o sistema

**Notificações in-app:**
- Badge/contador no ícone de notificações
- Lista de notificações com data/hora e descrição da movimentação
- Marcar como lida ao clicar
- Marcar todas como lidas

### Casos de erro e bordas
- Credenciais do e-SAJ expiradas ou alteradas pelo usuário: notificar o advogado para recadastrar
- e-SAJ fora do ar ou inacessível: job tenta novamente na próxima janela, sem gerar erro para o usuário
- CAPTCHA ou bloqueio do e-SAJ: logar o erro, não tentar novamente por X minutos
- Processo sem movimentações novas: nenhuma notificação gerada
- Advogado sem processos na carteira: exibir estado vazio com instrução

---

## 7. Critérios de Aceite

| Funcionalidade | Critério |
|---|---|
| Cadastro | Usuário consegue criar conta e acessar o app em menos de 2 minutos |
| Credenciais e-SAJ | Sistema valida e salva credenciais, e inicia importação automaticamente |
| Importação | Todos os processos do advogado aparecem no painel após importação |
| Monitoramento | Nova movimentação em processo gera notificação in-app em até 1 ciclo de verificação |
| Notificação | Notificação exibe número do processo e descrição da movimentação |
| Detalhe do processo | Histórico completo de movimentações é exibido em ordem cronológica |
| Erro de credencial | Sistema exibe mensagem clara quando credenciais do e-SAJ são inválidas |

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
- **Linguagem:** Python
- **Abordagem:** API REST
- **Autenticação:** JWT (access token + refresh token)
- **Jobs/Agendamento:** a definir (Celery + Redis, APScheduler, ou similar)
- **Scraping:** Browser Use + Playwright (MVP) → requests HTTP diretas (otimização futura)

### Infra/Deploy
- **Plataforma:** Railway (frontend, backend e banco na mesma plataforma)
- **Ambientes:** dev (local) → prod (Railway)
- **Variáveis de ambiente:** gerenciadas pelo Railway (nunca hardcoded)
- **Banco de dados:** PostgreSQL via Railway (plugin nativo)
- Staging: fora do escopo do MVP — ir direto para prod com feature flags se necessário

### Integrações
- **e-SAJ (TJSP):** via scraping automatizado com as credenciais do advogado
- **Outros tribunais:** fora do escopo do MVP
- **E-mail:** fora do escopo do MVP (necessário para recuperação de senha — P1)
- **Pagamentos:** fora do escopo do MVP

---

## 9. Banco de Dados

**Banco:** PostgreSQL via Railway (plugin nativo)
**ORM:** A definir (SQLAlchemy ou Tortoise ORM para Python)

### Entidades principais

**users**
- id (PK)
- email (unique)
- password_hash
- name
- created_at
- updated_at

**tribunal_credentials**
- id (PK)
- user_id (FK → users)
- tribunal (ex: "esaj_tjsp")
- username (criptografado)
- password (criptografado)
- last_validated_at
- is_active
- created_at

**processos**
- id (PK)
- user_id (FK → users)
- tribunal
- numero_processo (ex: "1234567-89.2024.8.26.0001")
- classe_judicial
- assunto
- status
- last_synced_at
- created_at

**movimentacoes**
- id (PK)
- processo_id (FK → processos)
- data_movimentacao
- descricao
- is_new (flag para notificação)
- created_at

**notifications**
- id (PK)
- user_id (FK → users)
- processo_id (FK → processos)
- movimentacao_id (FK → movimentacoes)
- message
- is_read
- created_at

### Relacionamentos
- 1 user → N tribunal_credentials
- 1 user → N processos
- 1 processo → N movimentacoes
- 1 user → N notifications

---

## 10. UX/UI e Identidade Visual

- **Objetivo de estilo:** Light theme com navbar dark — painel principal limpo e branco, sidebar clara, header escuro como âncora visual. Profissional e denso em informação, adequado ao contexto jurídico. Sem elementos lúdicos ou infantis.
- **Tom:** Confiança, controle, eficiência operacional
- **Componentes base:** shadcn/ui (já definido na stack)
- **O que evitar:** Dark theme total, design excessivamente colorido, gamificação, estética startup-genérica

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

### Tipografia
- A definir — fonte sem serifa, peso variado para hierarquia (labels em uppercase com letter-spacing)

### Layout e Estrutura (baseado no mockup)
- **Sidebar lateral esquerda:** Lista de processos em acompanhamento (fixados pelo advogado)
- **Painel principal central/direito:** Detalhe do processo selecionado
- **Header fixo:** Nome do produto + status do serviço de auditoria
- Cards de processo exibem: tribunal (badge colorido), número, cliente, prazo (badge colorido) e última movimentação
- Detalhe do processo exibe: etapas judiciais em timeline + gabinete de documentos lado a lado

---

## 11. Qualidade, Segurança e Operação

### Segurança
- Credenciais do e-SAJ armazenadas criptografadas no banco (nunca em plaintext)
- Autenticação via JWT com expiração e refresh token
- Rate limiting nas rotas de autenticação
- Variáveis sensíveis via variáveis de ambiente (nunca no código)
- HTTPS obrigatório em produção
- Validação de inputs no backend (nunca confiar só no frontend)

### Requisitos não-funcionais
- Performance: listagem de processos carrega em menos de 2 segundos
- Acessibilidade: ao menos contraste adequado e navegação por teclado nos fluxos principais
- SEO: não aplicável (app autenticado)

### Observabilidade
- Logs de erros nos jobs de scraping (falhas, timeouts, bloqueios)
- Log de eventos críticos: login, cadastro de credenciais, importação de processos
- Métricas mínimas: jobs executados, jobs com falha, processos monitorados

### Estratégia de testes
- Unitários: funções de parsing HTML → JSON (crítico — lógica do scraping)
- Integração: fluxo de autenticação + rotas protegidas
- E2E: fluxo crítico completo (cadastro → credenciais → ver processos → ver notificação)

---

## 12. Decisões em Aberto

| Decisão | Opções | Prazo para decidir |
|---|---|---|
| Orquestração de jobs | Celery + Redis, APScheduler, Railway Cron | Antes de implementar o scraping |
| Modelo de monetização | Assinatura mensal, por processo, freemium | Pré-lançamento |
| Frequência de sincronização | A cada 3h, 6h, 12h? | Antes de implementar o job |

### Decisões já tomadas
| Decisão | Escolha |
|---|---|
| Banco de dados | PostgreSQL (Railway plugin) |
| Deploy / infra | Railway (backend + banco + frontend) |
| Design system | Dark theme — paleta definida na seção 10 |

---

*Última atualização: junho/2026*

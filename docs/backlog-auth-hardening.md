# Backlog — Hardening de Auth (itens 7+)

> Origem: code review do módulo de autenticação (Etapas 3–4). Itens 1–6 do review já foram corrigidos — ver `docs/modulos/auth.md` (histórico) e os ADRs 003/004. Este arquivo lista o que ficou de fora daquela rodada, com contexto e prioridade sugerida.

---

## Prioridade alta

### Equalizar timing de `recuperar-senha`

O fix 5 desta rodada equalizou o timing do **login** (`verify_password_or_dummy`). `/auth/recuperar-senha` ainda retorna mais rápido quando o e-mail não existe (pula o `UPDATE` de tokens antigos + `INSERT` do novo token). Mais invasivo de corrigir sem custo de complexidade real (teria que simular trabalho de DB), e o risco é menor que no login — mensagem de resposta já é genérica. Avaliar se compensa antes de expor a um público maior.

---

## Prioridade média

### `FRONTEND_URL` dedicado

`settings.frontend_url` hoje é só a primeira entrada de `CORS_ORIGINS`. Funciona enquanto só houver uma origem de frontend, mas é um acoplamento implícito — se alguém reordenar ou adicionar uma segunda origem de CORS (ex.: preview deploy), o link de reset passa a apontar para o lugar errado sem nenhum erro visível. Criar uma variável de ambiente própria (`FRONTEND_URL`) e usá-la em vez de derivar de CORS.

### Normalizar pathname no interceptor do Axios

`frontend/src/lib/axios.ts` decide não disparar refresh comparando o `url` da request contra uma lista (`/auth/login`, `/auth/cadastro`, `/auth/refresh`). Se a `baseURL` ou algum call-site um dia usar URL absoluta ou path com trailing slash, a comparação por igualdade de string falha silenciosamente. Trocar por comparação de `pathname` normalizado (`new URL(url, baseURL).pathname`).

### Retry/UX quando `POST /auth/logout` falha

`Navbar.tsx` chama `logout()` e só então limpa o estado local. Se a request falhar (rede, 5xx), hoje não há tratamento explícito — o cookie de refresh pode sobreviver no navegador mesmo com o usuário "deslogado" na UI. Definir comportamento: limpar o estado local sempre (best-effort) e, opcionalmente, avisar o usuário que a sessão pode continuar ativa em outro lugar.

---

## Prioridade baixa / cosmético

### Remover `?token=` da URL após leitura

`frontend/src/routes/redefinir-senha.tsx` lê o token da query string mas não o remove do histórico do navegador. Um token de reset usado (ou abandonado) fica no histórico local do navegador do usuário. Usar `history.replaceState` ou navegação do TanStack Router para limpar o parâmetro depois de capturá-lo.

### Refresh proativo usando `expires_in`

Hoje o refresh só acontece reativamente, em resposta a um 401. Poderia ser agendado proativamente (`setTimeout` baseado em `expires_in`) para evitar que a primeira request depois de um período ocioso sempre pague o custo de um round-trip extra de refresh + retry.

### Bootstrap: retry em falha de rede

`ensureSessionRestored()` (`lib/session-bootstrap.ts`) trata falha do `/auth/refresh` como "sem sessão" — inclusive quando a falha é de rede (offline, timeout), não de token inválido. Um usuário que abre o app momentaneamente offline é deslogado sem necessidade. Diferenciar erro de rede de 401 e, no primeiro caso, permitir nova tentativa.

### Mensagens de sucesso hardcoded no frontend

Algumas mensagens de sucesso (ex.: "Sessão encerrada") existem tanto no backend (`MessageSchema.message`) quanto implicitamente no frontend. Não é um bug, mas vale revisar se o frontend deveria sempre exibir `response.message` em vez de strings próprias, para manter uma única fonte de texto.

### `React.lazy` nas rotas do painel

`security.mdc` recomenda `React.lazy` + `Suspense` nas rotas protegidas para não expor lógica do painel no bundle a um visitante não autenticado. Ainda não aplicado nas rotas de `processos`/`elaboracao`. Baixo risco (o backend já é a fonte de verdade), mas alinhado com a diretriz do projeto.

### Cadastro: 409 vs anti-enumeração

`/auth/cadastro` retorna `409 Conflict` explícito quando o e-mail já existe — diferente de login/recuperar-senha, que são deliberadamente genéricos para não vazar quais e-mails estão cadastrados. Isso é uma decisão de produto (UX de cadastro normalmente quer avisar "e-mail já em uso"), não um bug, mas vale documentar a escolha explicitamente ou revisitar se o time decidir priorizar anti-enumeração também aqui.

---

## Como usar este backlog

Ao pegar um item, mover a linha correspondente para `docs/modulos/auth.md` (histórico de mudanças) quando implementado, e remover deste arquivo.

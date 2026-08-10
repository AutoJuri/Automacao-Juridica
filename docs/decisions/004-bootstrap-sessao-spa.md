# ADR-004: Restauração silenciosa de sessão no boot da SPA

**Data:** 2026-08-09
**Status:** Aceito

---

## Contexto

O PRD e o `security.mdc` mandam: access token só em memória (Zustand) e refresh token em cookie HttpOnly. Consequência: um F5 descarta o access token mesmo com cookie válido. Sem um passo explícito no boot, as guardas de rota (`requireAuth`) redirecionariam para `/login` em todo reload de página autenticada.

Além disso, o backend **rotaciona** o refresh token a cada `POST /auth/refresh`. Duas chamadas simultâneas com o mesmo cookie fazem a segunda falhar (token já revogado).

## Decisão

1. No `beforeLoad` de `__root.tsx`, aguardar `ensureSessionRestored()` — uma tentativa única de `POST /auth/refresh` por carregamento da SPA, antes de qualquer rota filha decidir redirecionar.
2. Centralizar a renovação em `refreshAccessToken()` (`lib/axios.ts`) com promise memoizada, reutilizada pelo interceptor de 401 e pelo bootstrap.
3. Proteger rotas com funções puras `requireAuth` / `requireGuest` no `beforeLoad` do TanStack Router — sem componente `ProtectedRoute` paralelo.

## Alternativas consideradas

- **Persistir o access token em `sessionStorage`:** descartado — viola a regra de segurança (XSS lê storage).
- **Só renovar no interceptor quando a primeira request der 401:** descartado — a guarda de rota rodaria antes e expulsaria o usuário no F5, mesmo com cookie válido.
- **Layout route `_authenticated` do TanStack Router:** adiado — DRY via `route-guards.ts` por rota é suficiente nesta etapa; layout route pode entrar depois sem mudar o contrato de sessão.

## Consequências

- Reload e abertura de nova aba mantêm o usuário logado enquanto o cookie de refresh for válido.
- Requests concorrentes que disparam 401 compartilham um único refresh — compatível com a rotação no backend.
- Visitante sem cookie vê um 401 silencioso no boot (esperado) e segue para as rotas públicas.
- Qualquer tela futura protegida deve usar `requireAuth` (ou um layout que o chame), nunca um segundo mecanismo de guarda.

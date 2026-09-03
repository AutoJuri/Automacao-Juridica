# ADR-014: Chrome em dois eixos (áreas no topo, operação em Gerências)

**Data:** 2026-09-03
**Status:** Aceito

---

## Contexto

O PRD descrevia um painel com navbar de seções operacionais (autos, consulta, intimações, pautas). O produto passou a precisar de áreas maiores (Gerências, Elaborações, Drive, Tarefas) sem misturar isso com o acompanhamento diário do e-SAJ. Colocar tudo na mesma barra deixava o menu denso e o ícone de Andamentos colado na logo.

## Decisão

A SPA autenticada usa dois eixos:

1. **Navbar superior** — quatro áreas: Gerências, Elaborações, Drive e Tarefas. Logo, sino, Configurações e Sair ficam fora desse grupo.
2. **Rail esquerda** — só existe **dentro de Gerências**. Contém Andamentos, Consultas, Intimações, Audiências e Push Robôs. Fica abaixo da navbar.

Gerências abre Andamentos (`/`). `/gerencias` redireciona para `/`. Elaborações no topo também cobre a minuta `/elaboracao/$processoId` (rota distinta de `/elaboracoes`). Drive e Tarefas são placeholders autenticados, sem rail.

## Alternativas consideradas

- Manter as seções operacionais na navbar e as áreas novas noutro menu — descartado: a barra já estava cheia e o escopo novo não cabia.
- Rail visível em todas as áreas — descartado: Drive/Tarefas/Elaborações não têm módulos laterais; a rail sem contexto polui.
- Aninhar URLs em `/gerencias/andamentos` — descartado por agora: as rotas já existentes (`/`, `/consulta-pasta`, …) continuam; muda só o chrome.

## Consequências

- Fica mais fácil crescer Elaborações/Drive/Tarefas sem competir com o ciclo e-SAJ na mesma barra.
- Quem entra em Elaborações perde a rail de propósito — voltar ao acompanhamento é clicar Gerências.
- A minuta de um processo continua em `/elaboracao/$processoId`; a lista `/elaboracoes` ainda está vazia.

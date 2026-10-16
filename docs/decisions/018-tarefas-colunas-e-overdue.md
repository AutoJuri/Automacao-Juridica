# ADR-018: Tarefas com colunas do quadro e prazo vencido calculado

**Data:** 2026-10-03
**Status:** Aceito

---

## Contexto

O PRD descreve `tasks.column` como `todo|in_progress|done` e um job à 0h30 que grava `is_overdue`. A UI do Kanban, já em uso, deixa o usuário nomear até quatro colunas. O prazo na tela é um dia (`YYYY-MM-DD`), não um instante.

## Decisão

- Cada quadro (pessoal ou uma organização) tem de 1 a 4 linhas em `kanban_columns`. A tarefa aponta para `column_id`.
- Uma coluna do quadro pode ser a de conclusão (`is_done`). No máximo uma. O padrão "Concluído" já nasce marcada. Entrar nela grava `completed_at`; sair limpa.
- `due_date` é `DATE`. `is_overdue` não é coluna: a leitura calcula `due_date < hoje em America/Sao_Paulo` e `completed_at` nulo.
- Não há job de tarefas. `priority` continua fora desta entrega.
- `tasks.column_id` é `ON DELETE RESTRICT`. Excluir a organização apaga as tarefas antes das colunas, num trigger `BEFORE DELETE`, para o CASCADE da organização não esbarrar nessa constraint.

## Alternativas consideradas

- **Três colunas fixas do PRD:** descartado — a tela já permite renomear e ter uma quarta coluna.
- **Gravar `is_overdue` à 0h30:** descartado — o valor fica defasado o dia inteiro e o cálculo na leitura é barato.
- **`due_date` como timestamp:** descartado — a UI não pede hora.

## Consequências

- Quando a visibilidade de processos por papel existir, só muda a checagem do vínculo. Hoje o processo ligado precisa ser do usuário que está gravando a tarefa.
- Marcar outra coluna como conclusão tira a marca da anterior e limpa `completed_at` das tarefas que estavam nela.
- O histórico desta branch encadeia a migration de organizações em `e5b3f7a2c916`. A revisão `f1c8a4e2b7d0` está no banco local, mas o arquivo não está nesta branch; o ponteiro local foi alinhado em `b4e8c1a09f27` porque as tabelas de organização já existiam.
- Em 2026-10-06 o nome e a frase do quadro passaram para `kanban_boards`, uma linha por contexto. Sem linha, a API devolve "Tarefas" e a frase padrão. Quem configura as colunas (no pessoal, o dono; na organização, Owner e Admin) grava pelo `PATCH` do board.
- Em 2026-10-07 a coluna de conclusão passou a sair em páginas de 10, com `task_count` no quadro e um GET só dessa coluna. As outras colunas continuam inteiras. Uma tarefa que o membro não enxerga responde 404, o mesmo de um id inexistente.

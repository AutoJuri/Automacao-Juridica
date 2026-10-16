# Módulo: Tarefas (Kanban)

> Última atualização: 2026-10-07
> Camada: Backend / Frontend

---

## O que este módulo faz

Guarda e exibe o quadro de tarefas do contexto pessoal e de cada organização. O usuário cria até quatro colunas, cria tarefas com título, descrição, responsável, processo opcional e prazo, e move os cards. No escritório, Owner e Admin veem todas as tarefas; Advogado, Assistente e Estagiário veem só as que criaram ou que lhes foram atribuídas. A coluna de conclusão chega com as dez primeiras; o restante entra pelo botão "Carregar mais".

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/task.py` | `KanbanColumn`, `KanbanBoard` e `Task` |
| `backend/app/services/tasks.py` | Quadro, colunas, mover, vínculo a processo e notificações |
| `backend/app/api/tasks.py` | Rotas pessoais em `/tasks` e de organização em `/organizations/{org_id}` |
| `backend/app/core/permissions.py` | Mover, excluir e filtro de visibilidade |
| `frontend/src/features/tarefas/tarefas.api.ts` | Cliente HTTP e conversão para o quadro da tela |
| `frontend/src/features/tarefas/tarefas.queries.ts` | TanStack Query; mover usa update otimista |
| `frontend/src/features/tarefas/tarefas.board.ts` | Regras de UX: limite, renomear, soltar o card e prazo |
| `frontend/src/features/tarefas/KanbanBoard.tsx` | Arrastar com `@dnd-kit/core` e `@dnd-kit/sortable`. O clique abre o detalhe; o arraste só começa depois de mover o ponteiro. O card também avança para a coluna seguinte ou salta para a de conclusão. Na coluna de conclusão, "Carregar mais" pede a página seguinte |
| `frontend/src/features/tarefas/TarefaCard.tsx` | Card com exclusão em dois cliques, avanço para a coluna seguinte e salto para a conclusão |
| `frontend/src/features/tarefas/TarefaDetalheDialog.tsx` | Modal de leitura, com editar, excluir e link do processo para Gerências (`/?processo=`) |
| `frontend/src/features/tarefas/QuadroCabecalho.tsx` | Nome e frase do quadro, editáveis por quem configura as colunas |

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/tasks/board` | Quadro pessoal, com `title` e `description`. Na primeira leitura cria as três colunas padrão | Sim |
| PATCH | `/tasks/board` | Grava o nome e a frase do quadro pessoal | Sim |
| POST | `/tasks` | Cria tarefa pessoal. O responsável é o usuário do JWT | Sim |
| PATCH | `/tasks/{id}` | Edita título, descrição, prazo e processo | Sim |
| POST | `/tasks/{id}/move` | Move e reordena. `position` é o índice na coluna de destino | Sim |
| DELETE | `/tasks/{id}` | Exclui a tarefa pessoal | Sim |
| POST | `/tasks/columns` | Nova coluna, até quatro | Sim |
| PATCH | `/tasks/columns/{id}` | Renomeia ou marca `is_done` | Sim |
| DELETE | `/tasks/columns/{id}` | Remove coluna vazia que não seja a última | Sim |
| GET | `/organizations/{org_id}/tasks/board` | Quadro da organização, filtrado pelo papel | Sim |
| PATCH | `/organizations/{org_id}/tasks/board` | Nome e frase do quadro. Só Owner e Admin | Sim |
| POST | `/organizations/{org_id}/tasks` | Cria tarefa. `assigned_to_member_id` precisa ser membro | Sim |
| PATCH | `/organizations/{org_id}/tasks/{id}` | Edita. Advogado e assistente só a própria ou a atribuída | Sim |
| POST | `/organizations/{org_id}/tasks/{id}/move` | Move com a mesma regra de edição | Sim |
| DELETE | `/organizations/{org_id}/tasks/{id}` | Exclui. Advogado e assistente só se forem o autor | Sim |
| POST | `/organizations/{org_id}/kanban/columns` | Nova coluna. Só Owner e Admin | Sim |
| PATCH | `/organizations/{org_id}/kanban/columns/{id}` | Renomeia ou define a coluna de conclusão | Sim |
| DELETE | `/organizations/{org_id}/kanban/columns/{id}` | Remove coluna vazia. Só Owner e Admin | Sim |
| GET | `/tasks/columns/{id}/tasks?offset=` | Próximas dez tarefas da coluna de conclusão pessoal. Outra coluna responde 404 | Sim |
| GET | `/organizations/{org_id}/kanban/columns/{id}/tasks?offset=` | O mesmo no quadro da organização, com o filtro de visibilidade | Sim |

> Toda rota usa `Depends(get_current_user)`. Nas rotas de organização, `get_current_org_member` confirma a membership do path. `user_id` não entra no body. Tarefa de outro quadro, ou que o membro não enxerga, responde 404. Tarefa visível que o membro não pode excluir responde 403. O tamanho da página é fixo em 10 no servidor; o cliente só manda o `offset`.

---

## Funções e hooks públicos

| Nome | Arquivo | Descrição |
|---|---|---|
| `useQuadroTarefas` | `tarefas.queries.ts` | Carrega o quadro do contexto ativo |
| `useMoverTarefa` | `tarefas.queries.ts` | Move com update otimista e volta atrás se a API recusar |
| `useCarregarMaisConcluidas` | `tarefas.queries.ts` | Acrescenta a página seguinte na coluna de conclusão, sem recarregar o quadro |
| `moverTarefa` | `tarefas.board.ts` | Calcula a ordem local antes do POST |
| `estaAtrasada` | `tarefas.board.ts` | Prazo anterior a hoje em America/Sao_Paulo |
| `pode_editar_ou_mover_tarefa` | `permissions.py` | Owner/Admin sempre; demais se criaram ou receberam |
| `filtro_visibilidade_tarefas` | `permissions.py` | Cláusula SQL da listagem na organização |

---

## Padrões seguidos neste módulo

- **Autenticação:** `Depends(get_current_user)` em toda rota
- **Organização:** membership no banco antes de ler ou gravar; papel em `core/permissions.py`, nunca no JWT
- **Isolamento:** pessoal filtra `organization_id IS NULL` e `created_by`; organização filtra `organization_id` do path. As duas queries não se misturam
- **Visibilidade:** Owner/Admin veem todas as tarefas da org; Advogado, Assistente e Estagiário só autor ou responsável. O filtro está no WHERE, inclusive na leitura de uma tarefa pelo id: quem não enxerga recebe 404
- **Conclusão:** o quadro devolve no máximo 10 tarefas dessa coluna e o total em `task_count`. As outras colunas vêm inteiras. "Carregar mais" usa o mesmo filtro e o mesmo limite
- **Resposta:** `BoardSchema` e `TaskPublicSchema`. O processo vinculado sai só como `id` e `nu_processo`. Sem e-mail
- **Responsável:** a API recebe o id do membership e grava o `user_id`, depois de confirmar que é membro da mesma organização
- **Processo:** só um processo do usuário que está gravando (`Processo.user_id`). Outro id responde 404
- **Colunas:** no máximo 4, checado sob `SELECT … FOR UPDATE` na organização ou no usuário. A coluna de conclusão é no máximo uma
- **Atraso:** calculado na leitura. Tarefa com `completed_at` não está vencida
- **Notificação:** `task_atribuida` para o responsável quando não é quem agiu; `task_concluida` para o autor quando outra pessoa conclui e o autor não é o responsável. O texto é o título da tarefa, sem número de processo
- **Frontend:** esconder o botão de coluna é só visual. 403, 404 e 409 viram mensagem fixa, sem repetir o corpo da API
- Título e descrição são texto do React, sem `dangerouslySetInnerHTML`

---

## Modelo de dados relacionado

`kanban_columns` tem `organization_id` ou `user_id`, nunca os dois. `kanban_boards` guarda o nome e a frase daquele mesmo contexto; sem linha, a API devolve "Tarefas" e a frase padrão. `tasks.column_id` não apaga em cascata (`RESTRICT`). Excluir a organização dispara o trigger `apagar_quadro_da_organizacao`, que remove as tarefas e depois as colunas. A linha de `kanban_boards` sai pelo `ON DELETE CASCADE`.

```python
class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[uuid.UUID | None]
    column_id: Mapped[uuid.UUID]
    position: Mapped[int]
    title: Mapped[str]
    description: Mapped[str]
    created_by: Mapped[uuid.UUID]
    assigned_to: Mapped[uuid.UUID | None]
    processo_id: Mapped[uuid.UUID | None]
    due_date: Mapped[date | None]
    completed_at: Mapped[datetime | None]
```

`notifications` ganhou `task_id` e `organization_id`, os dois nulos, com `ON DELETE SET NULL`.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| `auth` | `current_user` em toda operação |
| `organizacoes` | Membership, papel e lista de membros para o responsável |
| `processos` | Vínculo opcional, só com processo do próprio usuário |
| `notifications` | Avisos `task_atribuida` e `task_concluida` |

---

## O que NÃO fazer aqui

- Não aceitar `user_id` ou `organization_id` no body. O responsável da organização entra como id de membership.
- Não listar tarefa pessoal e de organização na mesma query.
- Não filtrar visibilidade em Python depois de buscar o quadro inteiro.
- Não responder 403 para uma tarefa que o membro não enxerga. 403 fica para quem vê a tarefa e não tem a ação (por exemplo, o responsável que não é o autor e tenta excluir).
- Não deixar o cliente escolher quantas tarefas a página traz. O limite é 10 no serviço.
- Não gravar `is_overdue`. O valor muda de um dia para o outro sem job.
- Não devolver e-mail, senha, cookie ou o processo inteiro na tarefa.
- Não colocar o número do processo no texto da notificação.
- Não apagar coluna com tarefa. A API responde 409; o banco recusa com `RESTRICT`.
- Não tratar o papel guardado no frontend como autorização.
- Não instalar `@dnd-kit/react` no lugar dos pacotes estáveis.
- Não renderizar título ou descrição com HTML.
- Não colocar comentário, anexo ou prioridade nesta etapa.

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-10-02 | Quadro Kanban só na UI, sem persistência |
| 2026-10-03 | API, tabelas, permissões, notificações e a tela passou a gravar no backend (ADR-018) |
| 2026-10-06 | Nome do quadro persistido, modal de detalhe com exclusão, colunas ocupam a largura da página |
| 2026-10-06 | Atalhos no card para a próxima coluna e para a conclusão; colunas com cor por papel |
| 2026-10-06 | Com 4 colunas o botão de limite sai e as colunas dividem a largura do quadro |
| 2026-10-07 | Documenta o card, o link do processo e a tabela `kanban_boards` |
| 2026-10-07 | Coluna de conclusão pagina de 10 em 10. Tarefa invisível passa a responder 404 |

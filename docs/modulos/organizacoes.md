# Módulo: Organizações e Convites

> Última atualização: 2026-10-07
> Camada: Backend / Frontend

---

## O que este módulo faz

Permite que um usuário autenticado crie um escritório, vire Owner e convide outras pessoas com papel (Admin, Advogado, Assistente ou Estagiário). Owner e Admin gerenciam membros. O header troca o contexto entre Pessoal e uma organização. Esse id ativo fica só na memória e no `sessionStorage` — não autoriza nada. Processos e credenciais continuam pessoais. O quadro de tarefas persiste no banco e troca junto com o contexto (`/docs/modulos/tarefas.md`).

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/organization.py` | Tabelas `organizations`, `organization_members`, `organization_invites` e constantes de papel |
| `backend/app/core/permissions.py` | Membership do path e `require_role` |
| `backend/app/services/organizations.py` | Slug, convite (hash + validade), transferência e aceite |
| `backend/app/api/organizations.py` | Rotas `/organizations` |
| `backend/app/schemas/organization.py` | Request/response sem token |
| `backend/app/db/migrations/versions/b4e8c1a09f27_*.py` | Migration (revisa `e5b3f7a2c916`) |
| `frontend/src/features/organizations/` | API client, seletor, membros, convites |
| `frontend/src/store/org.store.ts` | Organização ativa em memória + preferência em `sessionStorage` |
| `frontend/src/routes/organizacoes.$orgId.tsx` | Página de membros |
| `frontend/src/routes/convites.tsx` | Convites recebidos |
| `frontend/src/routes/convite.$token.tsx` | Página pública do link |

---

## Endpoints

| Método | Rota | Descrição | Auth | Rate limit |
|---|---|---|---|---|
| GET | `/organizations` | Organizações do usuário | Bearer | — |
| POST | `/organizations` | Cria e torna o usuário Owner | Bearer | — |
| GET | `/organizations/{org_id}` | Detalhe, se for membro | Bearer | — |
| PATCH | `/organizations/{org_id}` | Renomeia (slug não muda) | Bearer, Owner/Admin | — |
| DELETE | `/organizations/{org_id}` | Exclui a organização | Bearer, Owner | — |
| GET | `/organizations/{org_id}/members` | Membros (nome, e-mail, papel) | Bearer, membro | — |
| PATCH | `/organizations/{org_id}/members/{member_id}` | Troca papel, nunca o Owner e nunca para Owner | Bearer, Owner/Admin | — |
| DELETE | `/organizations/{org_id}/members/{member_id}` | Remove outro membro ou sai (não-Owner) | Bearer, membro | — |
| POST | `/organizations/{org_id}/members/{member_id}/transfer-ownership` | Alvo vira Owner, Owner atual vira Admin | Bearer, Owner | — |
| GET | `/organizations/{org_id}/invites` | Pendentes, sem token | Bearer, Owner/Admin | — |
| POST | `/organizations/{org_id}/invites` | Convida ou renova (token antigo morre) | Bearer, Owner/Admin | — |
| DELETE | `/organizations/{org_id}/invites/{invite_id}` | Cancela | Bearer, Owner/Admin | — |
| GET | `/organizations/invites/received` | Pendentes do e-mail da conta, sem token | Bearer | — |
| POST | `/organizations/invites/received/{invite_id}/accept` | Aceita | Bearer | 10/hora por IP |
| POST | `/organizations/invites/received/{invite_id}/decline` | Recusa | Bearer | 10/hora por IP |
| GET | `/organizations/invites/{token}` | Preview público | Não | 10/hora por IP |
| POST | `/organizations/invites/{token}/accept` | Aceita se o e-mail da conta bater | Bearer | 10/hora por IP |
| POST | `/organizations/invites/{token}/decline` | Recusa se o e-mail da conta bater | Bearer | 10/hora por IP |

> `user_id` vem só do JWT. `organization_id` no path não autoriza sozinho: `get_current_org_member` exige a linha em `organization_members`.
> Papel não entra no JWT.

---

## Funções e hooks públicos (frontend)

| Nome | Arquivo | Descrição |
|---|---|---|
| `OrgSwitcher` | `features/organizations/OrgSwitcher.tsx` | Seletor no header: Pessoal, organizações, criar, membros, convites |
| `destinoConvite` | `features/organizations/organizations.redirect.ts` | Aceita só `/convite/{uuid}` como redirect pós-login |
| `useOrgStore` | `store/org.store.ts` | Id da organização ativa. `null` é o contexto pessoal |

---

## Padrões seguidos neste módulo

- **Autenticação:** rotas de gestão usam `Depends(get_current_user)`. Preview do token é público.
- **Papel:** só `core/permissions.py`. Owner-only (excluir e transferir) é `require_role` com o conjunto do Owner. Estagiário entra no convite e na troca de papel, com o mesmo limite do Assistente: não convida, não configura o quadro e só vê tarefa que criou ou recebeu.
- **Resposta:** schemas Pydantic. Listagem de convite não tem `token` nem `token_hash`.
- **Entrada:** os schemas de criar organização, atualizar, mudar papel e convidar usam `extra="forbid"`. Campo desconhecido é rejeitado antes do serviço.
- **Token:** UUID v4 só no link. O banco guarda SHA-256 (`hash_token`). Ver ADR-017.
- **E-mail:** mesmo gate da ADR-003. Development loga o link; qualquer outro ambiente loga só o `user_id` de quem convidou, sem token e sem e-mail do convidado.
- **Notificação:** tipo `convite_org` para quem já tem conta. A mensagem não leva o token.
- **Contexto ativo:** memória + `sessionStorage`. Se o id não estiver na lista da API, volta para Pessoal. Não substitui a checagem de membership.

---

## Modelo de dados relacionado

Papéis em `VARCHAR` (ADR-002): `owner`, `admin`, `advogado`, `assistente`, `estagiario`. O banco recusa outro valor. O cargo da conta (`users.cargo`) não é papel e não autoriza nada (ADR-020).

Convite pendente é único por `(organization_id, email)` enquanto `accepted_at` e `revoked_at` são nulos. Validade de 7 dias. Reenviar gira o `token_hash` e a expiração.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| `auth` | `current_user` e o mesmo hash de token opaco |
| `notifications` | Aviso in-app `convite_org` na tabela já existente |

---

## O que NÃO fazer aqui

- Não colocar `role`, `organization_id` ou `cargo` no JWT.
- Não usar `users.cargo` para autorizar. O cargo é só o perfil da conta.
- Não confiar no id de organização do `sessionStorage` para autorizar.
- Não devolver o token do convite em listagem, notificação ou resposta de criação.
- Não logar o token fora de `APP_ENV=development`, nem o e-mail do convidado.
- Não promover a Owner pelo convite ou pelo PATCH de papel — só a transferência.
- Não filtrar processos ou credenciais por organização nesta etapa.
- Não usar o OAuth do e-mail do advogado para enviar o convite.

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-10-02 | Implementação inicial: CRUD de organização, membros, convites e seletor de contexto |
| 2026-10-07 | Esclarece que o id ativo é só UX e que o quadro de tarefas persiste no banco |
| 2026-10-07 | Schemas de entrada recusam campo extra |
| 2026-10-07 | Papel `estagiario` no convite e na troca de papel, com o limite do Assistente |

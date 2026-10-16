# ADR-020: Cargo do perfil separado do papel na organização

**Data:** 2026-10-07
**Status:** Aceito

---

## Contexto

O escritório precisa convidar um estagiário, e a pessoa que cria a conta quer registrar o que faz (advogado, assistente ou estagiário). Esses dois dados parecem a mesma lista, mas um autoriza acesso dentro da organização e o outro só descreve a conta.

## Decisão

- O papel em `organization_members` e `organization_invites` ganha `estagiario`. Ele pode ser convidado e ter o papel trocado por Owner ou Admin. Não convida, não configura o quadro e só vê tarefa que criou ou que lhe foi atribuída — o mesmo limite do assistente.
- `users.cargo` guarda `advogado`, `assistente` ou `estagiario`. O cadastro exige um desses. Conta criada antes da coluna fica com `null`.
- O cargo não entra no JWT e nenhuma rota lê `users.cargo` para autorizar. O papel continua vindo de `organization_members` em cada request.

## Alternativas consideradas

- **Usar o cargo da conta como papel ao entrar na organização:** descartado — a pessoa pode ser advogada no perfil e estagiária em um escritório, ou o contrário. Quem define o acesso é quem convida.
- **Dar ao estagiário um conjunto de permissões diferente do assistente:** descartado nesta etapa — o pedido é ter o rótulo no convite e no perfil, sem uma matriz nova.

## Consequências

- O banco recusa cargo e papel fora das listas (`ck_users_cargo`, `ck_organization_members_role`, `ck_organization_invites_role`).
- Uma restrição futura só do estagiário (por exemplo, não atribuir tarefa) muda `core/permissions.py`, não o cargo da conta.

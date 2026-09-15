# ADR-002: VARCHAR + constantes Python em vez de ENUM nativo do Postgres

**Data:** 2026-08-05
**Status:** Aceito

---

## Contexto

Vários campos do schema representam estados fechados (`tribunal_sessions.status`, `notifications.tipo`, `job_logs.tipo` / `status`, `email_provider`). O Postgres oferece tipo `ENUM` nativo, mas alterar o conjunto de valores exige migration (e, em algumas versões/fluxos, cuidados com `ALTER TYPE` e downtime). O PRD já descreve esses campos como `VARCHAR`; faltava deixar explícito o padrão de validação no código.

## Decisão

Persistir estados como `String` (VARCHAR) no banco e declarar os valores válidos como constantes Python no arquivo do model correspondente (`SESSION_STATUSES`, `NOTIFICATION_TIPOS`, `JOB_TIPOS`, etc.).

A validação de domínio acontece na camada de aplicação (Pydantic / services), não no tipo do Postgres.

## Alternativas consideradas

- **ENUM nativo do Postgres:** descartado — cada novo status (ex.: um novo estado de sessão) gera migration e risco operacional desnecessário no MVP.
- **Tabela de lookup (`status_types`):** descartado por over-engineering nesta fase; os conjuntos são pequenos e estáveis o suficiente para constantes.

## Consequências

- Adicionar um novo valor de status é mudança de código (e eventual validação Pydantic), sem migration de tipo.
- O banco não rejeita sozinho um valor inválido escrito por bug — a responsabilidade fica na API/services (aceitável no MVP com testes e schemas).
- Documentação e autocomplete ficam nas constantes exportadas pelos modules de model.

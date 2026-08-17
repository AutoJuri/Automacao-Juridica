# ADR-007: `TribunalSession.cookie_encrypted` nullable

**Data:** 2026-08-13
**Status:** Aceito

---

## Contexto

A Etapa 6 introduz a validação real de credenciais do e-SAJ via Playwright, disparada em background logo após `POST /credentials/esaj`. Para o frontend conseguir mostrar "validando..." via polling em `GET /credentials/status`, é preciso existir uma linha de `TribunalSession` com `status="reauth_pendente"` **antes** do login no e-SAJ acontecer — e, em qualquer um dos cenários de falha (`credencial_invalida`, `email_desconectado`, `portal_indisponivel`, `bloqueado`), essa linha continua existindo, mas sem nenhum cookie de sessão para guardar: o login nunca chegou a completar com sucesso.

A coluna `cookie_encrypted` era `NOT NULL` desde o schema inicial, partindo da premissa (válida até a Etapa 5) de que uma `TribunalSession` só seria criada depois de um login já ter funcionado.

## Decisão

Tornar `TribunalSession.cookie_encrypted` nullable (`Mapped[bytes | None]`). O orquestrador (`credential_validation.validar_credencial_esaj`) cria a sessão com `cookie_encrypted=None` no início de cada tentativa e só preenche esse campo quando o login é bem-sucedido.

## Alternativas consideradas

- **Só criar a `TribunalSession` depois do primeiro login bem-sucedido:** rejeitada — o frontend perderia a capacidade de fazer polling de status enquanto a primeira validação ainda está rodando (ficaria sem `session_status` nenhum, indistinguível de "nunca tentou").
- **Coluna separada `status_pendente` numa tabela auxiliar, mantendo `cookie_encrypted` obrigatório na tabela principal:** adiciona uma tabela e uma junção extra só para representar um estado transitório — complexidade desproporcional.
- **Valor sentinela (bytes vazios) em vez de `NULL`:** pior que `NULL` — esconde a ausência de cookie por trás de um valor "criptografado" que decriptaria para uma string vazia, criando um caso especial silencioso em vez de um estado explícito.

## Consequências

- Todo código que lê `TribunalSession.cookie_encrypted` para uso real (ex.: futuros pipes de coleta, Etapa 7+) precisa checar `is not None` antes de decriptar — nunca assumir que uma sessão existente tem cookie válido.
- `status` continua sendo a fonte de verdade sobre se a sessão pode ser usada (`ativo` é o único status em que `cookie_encrypted` está garantidamente preenchido e válido) — `cookie_encrypted is None` nunca deve ser inferido a partir de outro campo.
- Migration `a46336bed1eb_torna_cookie_encrypted_nullable_em_.py` é aditiva e reversível (`downgrade` volta para `NOT NULL`), mas um `downgrade` só funcionaria de fato num banco sem nenhuma linha com `cookie_encrypted IS NULL` — aceitável, já que esta migration foi aplicada antes de existir dado em produção.

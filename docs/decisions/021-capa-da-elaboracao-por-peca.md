# ADR-021: Capa da elaboração por peça, com ou sem processo

**Data:** 2026-10-08
**Status:** Aceito

---

## Contexto

A minuta já existia em `/elaboracao/$processoId`, mas a seção Elaborações estava vazia. O advogado precisava achar o processo em Gerências para começar uma peça, e não havia como elaborar sem um processo do e-SAJ. O texto da minuta ainda não vai ao servidor: isso fica para a etapa da IA (ADR-016 e ADR-019).

A branch `feat/create-IA` (commit `847381b`, migration `e782fdd01295`) já previa a tabela `elaboracoes` com `processo_id` obrigatório, `peca` e colunas criptografadas. Esta etapa não traz essa branch.

## Decisão

- Uma elaboração é a capa: usuário, peça e ou um processo ou dados digitados (`titulo` e campos opcionais). O HTML fica no navegador.
- Um processo pode ter várias elaborações, uma por peça. Reabrir a mesma peça devolve a linha existente (200). Trocar a peça para uma que já existe naquele processo responde 409.
- "Para começar" lista só processos sem nenhuma linha em `elaboracoes`.
- A minuta abre em `/elaboracao/$elaboracaoId`. O botão Elaborar do processo cria ou reabre e navega para esse id.
- A lista é pessoal (`user_id` do JWT). Papel de organização não entra aqui.
- A migration `a9c4e2b7d1f6` cria a tabela quando ela não existe. Se o banco local já tinha `elaboracoes` no formato da branch de IA (`processo_id` obrigatório, `fatos_extras_encrypted`, `estilo_perfil_encrypted`), a mesma migration completa a capa: torna `processo_id` nulo, adiciona os campos manuais, troca o unique cheio pelo índice parcial e **não apaga** as colunas criptografadas.

## Alternativas consideradas

- **Uma elaboração por processo:** descartado — o mesmo processo pode ter contestação e apelação.
- **Abrir a minuta pelo id do processo:** descartado — duas peças do mesmo processo não caberiam na mesma URL.
- **Persistir o HTML agora:** descartado — o texto só precisa ir ao servidor quando a IA for ligada.

## Consequências

- Quando `feat/create-IA` entrar, a migration `e782fdd01295` não pode fazer `CREATE TABLE elaboracoes`. Ela vira um ALTER que adiciona `fatos_extras_encrypted`, `estilo_perfil_encrypted` e `elaboracao_versoes` somente se ainda não existirem.
- Banco novo desta branch não tem as colunas criptografadas. Banco que já passou pela branch de IA continua com elas, sem uso nesta etapa.
- Abrir a elaboração em outro computador mostra a capa e uma minuta vazia, até o texto ser persistido.

# ADR-005: Mascaramento de CPF sem decriptação (coluna `cpf_mascarado` em texto puro)

**Data:** 2026-08-11
**Status:** Aceito

---

## Contexto

O frontend precisa exibir o CPF cadastrado do advogado de forma parcial (ex.: `***.456.789-**`) para confirmar visualmente qual credencial está salva, sem nunca expor o CPF completo — conforme `security.mdc`. O CPF real vive só como `cpf_encrypted` (AES-256-GCM), e a regra do projeto é que dado sensível criptografado só pode ser decriptado em memória, no momento exato de uso por um job (Etapa 6, Playwright) — nunca a partir de uma requisição HTTP comum.

Se o endpoint `GET /credentials/status` precisasse decriptar `cpf_encrypted` toda vez só para montar a máscara, isso violaria essa regra: toda chamada do frontend abriria a chave AES em memória do processo web, numa rota que não tem relação nenhuma com o job de scraping.

## Decisão

Adicionar uma coluna `cpf_mascarado: str` em `TribunalCredential`, calculada **uma única vez** no momento do `POST /credentials/esaj` (quando o CPF em texto puro já está disponível na requisição, antes de ser descartado) e persistida em texto puro no banco. O endpoint de status só faz `SELECT cpf_mascarado` — nunca toca em `cpf_encrypted`.

## Alternativas consideradas

- **Decriptar sob demanda no `GET /status`:** rejeitada — contraria a regra de "decriptar só em memória, só no momento do job" e adiciona uma superfície de decriptação desnecessária, alcançável por qualquer requisição autenticada.
- **Calcular a máscara no frontend a partir de algo derivado do CPF:** não há como, o frontend nunca recebe nem os últimos dígitos do CPF de outra forma.
- **Não mascarar nada, só mostrar "CPF cadastrado" (booleano):** perderia a confirmação visual que ajuda o advogado a saber que o CPF certo foi salvo, especialmente em caso de erro de digitação.

## Consequências

- `cpf_mascarado` (formato `***.456.789-**`) fica em texto puro no banco, mas isso é aceitável: o próprio `security.mdc` usa esse formato como exemplo de dado seguro para exibição — 3 dígitos do meio de um CPF não são suficientes para identificar ou reconstruir o documento completo.
- Qualquer alteração de CPF (`POST /credentials/esaj` de novo) precisa recalcular e sobrescrever `cpf_mascarado` junto com `cpf_encrypted` — os dois campos são atualizados sempre juntos, nunca separadamente.
- Se um dia for necessário mascarar de outra forma (ex.: mostrar mais/menos dígitos), é só recalcular a partir do próximo cadastro — não há uma migração de dados retroativa possível sem decriptar todo o histórico (o que também não é um problema, dado que a tabela começa vazia nesta etapa).

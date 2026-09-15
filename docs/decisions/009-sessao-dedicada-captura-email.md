# ADR-009: Sessão SQLAlchemy dedicada para captura do código MFA

**Data:** 2026-08-17
**Status:** Aceito

---

## Contexto

O login no e-SAJ roda Playwright na API síncrona dentro de `asyncio.to_thread` (necessário no Windows: o event loop do uvicorn não lança subprocessos). O callback de MFA (`buscar_codigo_esaj`) é async e volta ao loop principal via `run_coroutine_threadsafe`.

O orquestrador envolve essa chamada em `asyncio.wait_for(..., timeout=60)`. Quando o timeout dispara, a coroutine é cancelada, mas a **thread do Playwright continua**. Se o callback de e-mail compartilhar a mesma `AsyncSession` do orquestrador, dois caminhos passam a usar a sessão ao mesmo tempo:

- o orquestrador marca a falha (`_marcar_falha` → `db.commit()`) e pode fechar o `async with SessionLocal()`;
- a thread ainda chama `buscar_codigo_esaj` → refresh do token OAuth → `db.commit()` na sessão já em uso ou já fechada.

Isso é corrida de sessão, não só um timeout mal mapeado.

## Decisão

`buscar_codigo_esaj` recebe só `user_id` (e `since` / `cancelado`). A cada iteração do polling ela abre a própria `SessionLocal`, recarrega a `TribunalCredential` no banco e commita o refresh do token OAuth nessa sessão isolada.

O orquestrador, ao estourar os 60s, seta um `asyncio.Event` (`cancelado`) que o loop de polling consulta — para de fazer GETs órfãos na API de e-mail. Não é necessário `asyncio.shield`: a thread descarta o resultado; o cookie só é persistido no caminho de sucesso do orquestrador.

## Alternativas consideradas

- **`asyncio.shield` + esperar a thread terminar antes de marcar falha:** evita a corrida, mas o frontend ficaria em `reauth_pendente` além dos 60s enquanto o Playwright não morre. Pior UX sem ganho de isolamento.
- **Manter a sessão compartilhada e só setar um flag de cancelamento:** o flag para o polling, mas um `commit` de refresh já em voo ainda usaria a sessão do orquestrador.
- **Playwright async no mesmo loop:** voltaria o `NotImplementedError` no Windows/uvicorn.

## Consequências

- Refresh do token OAuth e persistência de `email_oauth_token_encrypted` ficam na sessão da captura — o orquestrador não vê o objeto `TribunalCredential` atualizado em memória, o que é irrelevante (ele não reusa o token depois do login).
- Um login que complete na thread depois do timeout **não** grava cookie: o resultado é descartado. O advogado clica em Revalidar (ou o scheduler da Etapa 7 tenta de novo).
- Fica explícito no módulo: nunca passar a `AsyncSession` do orquestrador para código que roda (ou é chamado) a partir da thread do Playwright.

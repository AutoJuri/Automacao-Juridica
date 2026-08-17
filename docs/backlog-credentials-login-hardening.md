# Backlog — Hardening Credenciais / Login e-SAJ

Origem: code review das Etapas 5–6 (2026-08-17).

Itens 1–7 e 9 foram implementados em 2026-08-17. Restam só o lock multi-worker e o `jti` OAuth.

---

## Feito

1. `DELETE /credentials/esaj` apaga a `TribunalSession` do mesmo `user_id`/`tribunal`. `POST /esaj` invalida a sessão antiga (apaga se não há e-mail; `reauth_pendente` + cookie nulo se há).
2. `buscar_codigo_esaj` usa `SessionLocal` própria (ADR-009). Timeout de 60s seta `asyncio.Event` para parar o polling de e-mail.
3. Gmail lista com `q=from:tjsp.jus.br after:{epoch}` antes do `format=full`. Outlook lista sem `body` (`$select=id,from,receivedDateTime`) e só então busca o corpo.
4. `TribunalSession.anular_cookie()` zera `cookie_encrypted`/`expires_at` em falha, `reauth_pendente` e desconexão de e-mail. Cookie válido só existe com `status=ativo`.
5. `DELETE /credentials/email` marca `email_desconectado` e devolve `session_status`.
6. Botão “Remover credenciais” desabilitado enquanto `session_status === reauth_pendente`.
7. `GET /email/{provider}/authorize` limitado a 10/hora por IP; frontend mapeia 429.
9. `CodigoNaoEncontradoError` é `LoginEsajError("codigo_nao_encontrado")` com mensagem UX própria.

---

## Aberto

8. Lock de validação por `user_id` no banco quando houver múltiplos workers. O guard `_VALIDACOES_EM_ANDAMENTO` só cobre o processo atual (ADR-008).
10. State OAuth com `jti` one-time (opcional; o `code` do provedor já é one-time).

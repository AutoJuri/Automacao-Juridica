# ADR-003: Recuperação de senha via log do servidor (sem provedor de e-mail)

**Data:** 2026-08-09
**Status:** Aceito (temporário)

---

## Contexto

A Etapa 3 exige endpoint de recuperação de senha. O projeto ainda não tem provedor de e-mail da plataforma. O OAuth2 Gmail/Outlook do PRD existe só para capturar o código do e-SAJ (escopo readonly) — não deve ser usado para enviar e-mail da AdvogAtiva.

## Decisão

Implementar o fluxo completo de tokens (`password_reset_tokens`, endpoints `/auth/recuperar-senha` e `/auth/redefinir-senha`, tela `/redefinir-senha`), mas **não** enviar e-mail. O comportamento do log depende do ambiente (`settings.is_development`):

- **`APP_ENV=development`:** o backend escreve no log a URL completa, para permitir testar o fluxo localmente:

  ```
  {frontend_url}/redefinir-senha?token={token}
  ```

- **Qualquer outro ambiente (staging/produção):** o token **nunca** é logado — apenas `logger.info("Token de redefinição de senha gerado para user_id=%s", user.id)`. Sem provedor de e-mail configurado, a recuperação de senha fica de fato indisponível fora de development até a próxima etapa integrar o envio real.

A resposta HTTP continua genérica (“Se o e-mail estiver cadastrado…”) para não vazar existência de contas. Quando houver provedor, o log do link em development deve ser removido e substituído pelo envio real.

## Alternativas consideradas

- **Adiar recuperação de senha até existir SMTP/provedor:** descartado — a Etapa 3 pediu o endpoint e o frontend da Etapa 4 precisa do fluxo ponta a ponta.
- **Usar Gmail/Outlook OAuth2 do advogado para enviar o e-mail da plataforma:** descartado — escopo readonly, e misturaria identidade do advogado com e-mail transacional do produto.
- **Devolver o token na resposta HTTP em development:** descartado — fácil esquecer o bypass em produção e abre enumeração/abuso.

## Consequências

- Desenvolvimento e QA conseguem testar o fluxo copiando o link do log.
- Produção **não** loga (nem depende d)o token — o gate por `is_development` torna isso garantido pelo código, não só por convenção; integrar provedor (Resend, SES, etc.) é pré-requisito de go-live da recuperação.
- `settings.frontend_url` (primeira origem de `CORS_ORIGINS`) passa a ser contrato para montar links enviados ao usuário.
- Ver `docs/backlog-auth-hardening.md` para o item de equalizar timing entre e-mail existente/inexistente neste endpoint (fora do escopo desta ADR).

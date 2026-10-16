# ADR-017: Convite de organização com token hasheado e link só no log

**Data:** 2026-10-02
**Status:** Aceito

---

## Contexto

O PRD pede convite por e-mail com token UUID e validade de 7 dias. A plataforma ainda não tem provedor transacional — a recuperação de senha já segue a ADR-003 (link no log só em development). Guardar o UUID cru em `organization_invites.token` faria um vazamento do banco entregar links de convite ainda válidos.

## Decisão

- O link usa um UUID v4. O banco persiste só `token_hash` (SHA-256, o mesmo `hash_token` do refresh e do reset).
- Em `APP_ENV=development`, o log leva `{frontend_url}/convite/{token}` e o `user_id` de quem convidou.
- Fora de development, o log não leva token nem e-mail do convidado.
- Se o e-mail já tem conta, nasce uma notificação `convite_org` sem o token. O aceite autenticado usa o id do convite, não o segredo do link.
- Cancelar ou recusar grava `revoked_at`. O convite não é apagado e não volta a valer.

## Alternativas consideradas

- **Coluna `token` em claro, como no desenho do PRD:** descartado — o hash já é o padrão dos outros tokens opacos e não piora o fluxo do link.
- **Integrar Resend/SMTP nesta entrega:** descartado — a decisão desta etapa foi repetir a ADR-003 até existir provedor.
- **Devolver o token no JSON em development:** descartado — o mesmo risco da ADR-003 de o bypass vazar para produção.

## Consequências

- Quem não tem conta só consegue o link pelo log, em development. Em produção o convite fica sem entrega até haver provedor de e-mail.
- Trocar o provedor no futuro substitui `registrar_link_convite`, sem mudar a tabela.
- Reenviar o convite invalida o link anterior porque o hash é substituído.

# ADR-026: E-mail transacional da plataforma via Resend

**Data:** 2026-10-29
**Status:** Aceito

Substitui a entrega por log da ADR-003 e da ADR-017. O token de senha e o token de convite continuam só como hash no banco.

---

## Contexto

Recuperação de senha e convite de organização já geram um link de uso único. Sem provedor, esse link só aparecia no log em development. Em produção o usuário não recebia nada. O OAuth do Gmail/Outlook do advogado é somente leitura e serve para o código do e-SAJ. Não deve enviar e-mail da AdvogAtiva.

O plano gratuito do Resend cabe no volume destes dois fluxos: 100 e-mails por dia e 3.000 por mês, sem excedente. Aviso de intimação, movimentação e audiência continua no sino.

---

## Decisão

- O envio sai de `email_plataforma.py`, com `RESEND_API_KEY` e `EMAIL_FROM`. A chamada do SDK roda fora do event loop.
- Recuperação de senha manda um destinatário para `{frontend_url}/redefinir-senha?token=...`. A resposta HTTP continua genérica.
- Convite manda um destinatário para `{frontend_url}/convite/{token}`. Quem já tem conta continua com o aviso no sino, sem o token.
- Com a chave preenchida, o log leva o tipo do envio e o id devolvido pelo Resend. Não leva token, link, chave nem destinatário. Falha de envio também não leva esses dados e não muda a resposta HTTP.
- Sem a chave, em development o link segue no log. Fora de development o log só diz que o provedor está ausente.
- O nome da organização entra escapado no HTML.

---

## Alternativas consideradas

- **Seguir só com o log:** descartado. Produção não entrega o link.
- **Mandar pelo OAuth do advogado:** descartado. Escopo readonly e mistura a caixa do advogado com o e-mail do produto.
- **E-mail para cada andamento:** descartado nesta etapa. Estoura a cota gratuita e o sino já cobre o aviso.

---

## Consequências

- Produção só entrega de verdade com domínio verificado no Resend e `EMAIL_FROM` desse domínio. A URL `vercel.app` do frontend não serve de remetente.
- Sem chave, o comportamento local permanece o da ADR-003.
- Trocar de provedor substitui `email_plataforma.py`. As tabelas de token não mudam.

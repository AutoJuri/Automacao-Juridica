# ADR-006: `state` do OAuth2 como JWT assinado stateless

**Data:** 2026-08-11
**Status:** Aceito

---

## Contexto

O fluxo OAuth2 (Authorization Code) do Gmail e do Microsoft Graph termina com o provedor redirecionando o navegador do advogado para `GET /credentials/email/{provider}/callback?code=...&state=...`. Essa requisição é uma navegação pura de browser — **não** chega com o header `Authorization: Bearer` que autentica todas as outras rotas do backend. Sem esse header, o callback não tem, por padrão, nenhuma forma de saber para qual `user_id` aquele `code` pertence.

O parâmetro `state` do protocolo OAuth2 existe exatamente para isso: é um valor opaco que o servidor gera antes de redirecionar para o provedor, e que volta intacto no callback. Precisávamos de uma forma de gerar e validar esse valor sem introduzir uma tabela nova só para guardar "sessões de OAuth pendentes".

## Decisão

O `state` é um JWT assinado com o mesmo `JWT_SECRET` já usado para o access token da plataforma, com `type="oauth_state"`, `sub=user_id`, `provider`, um `nonce` aleatório e expiração curta (10 minutos). `create_oauth_state_token`/`decode_oauth_state_token` em `app/core/security.py` seguem o mesmo padrão de `create_access_token`/`decode_access_token`. Nenhuma linha é gravada no banco para representar "um fluxo de OAuth2 em andamento" — o próprio token assinado carrega tudo que o callback precisa, e sua assinatura garante que não foi forjado nem adulterado.

## Alternativas consideradas

- **Tabela `oauth_states` no banco** (`state` aleatório → `user_id`, `provider`, `expires_at`): funciona, mas adiciona uma tabela, uma migration e um job de limpeza só para um dado que vive 10 minutos — overhead desproporcional ao problema.
- **Guardar o `user_id` em sessão de servidor (cookie de sessão própria)**: o projeto não tem sessão de servidor em nenhum outro lugar (é JWT stateless em tudo), introduzir uma só para isso quebraria a consistência arquitetural.
- **`state` como UUID aleatório simples, sem assinatura**: obrigaria a ter uma tabela de qualquer forma (o UUID sozinho não carrega `user_id`), e ainda seria necessário validar que não foi adulterado.

## Consequências

- O `state` nunca precisa ser "limpo" do banco depois de usado — expira sozinho, como qualquer JWT.
- A validação do `state` reaproveita a infraestrutura de JWT já auditada do módulo de autenticação (mesma função de assinatura, mesmos testes de adulteração/expiração/tipo errado).
- Um `state` só pode ser gerado por quem já está autenticado (Bearer) no momento do `/authorize` — não existe endpoint que gere um `state` sem `current_user`.
- Limitação aceita: como não há registro no banco, não é possível "revogar" um `state` específico antes da expiração (ex.: se o advogado abrir `/authorize` duas vezes, os dois states continuam válidos até expirarem). Isso não é um risco de segurança — cada `state` só serve para completar exatamente um `code` de um provedor, uma única vez, e o pior cenário é o segundo callback simplesmente sobrescrever o token de e-mail salvo pelo primeiro.

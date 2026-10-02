# Módulo: IA da Elaboração

> Última atualização: 2026-10-01
> Camada: Backend / Frontend

---

## O que este módulo faz

Liga os botões que já existiam na tela `/elaboracao/$processoId` (fatos extras, **Elaborar**, chat, grifo de seleção, seletor de peça, upload de modelo) a um adapter de LLM plugável (ADR-016, Fases 1 a 4). O padrão do código é o **stub sem rede** (`LLM_PROVIDER=stub`): monta HTML/JSON determinístico e claramente rotulado como rascunho/heurística de teste. `openrouter` e `anthropic` estão implementados e só entram por variável de ambiente. Com OpenRouter ligado, o prompt de gerar leva a ficha real (CNJ, partes, fatos extras, minuta). Modelo com sufixo `:free` só segue em `APP_ENV=development`; fora disso a chamada é recusada antes do HTTP (503). As versões da minuta deixaram de ser só `localStorage` e passaram a ser dado do servidor, cifrado (AES-256-GCM), com histórico completo por sessão.

Fases 1 e 3 (2026-09-22): a tela de elaboração sugere **uma** peça a partir da intimação/movimentação mais recente, e o painel "Peça modelo específica" pode enviar o texto (TXT/colar) de um modelo à IA para extrair um **perfil de estilo** desta sessão — ambos alimentam o pacote enviado ao `gerar`, mas o seletor de peça e o upload continuam livres/opcionais. O card do processo não chama o modelo (2026-09-30): cada ficha aberta gastava um pedido da cota grátis.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/elaboracao.py` | `Elaboracao` (sessão por `user_id`+`processo_id`+`peca`, com `fatos_extras_encrypted` e `estilo_perfil_encrypted`) e `ElaboracaoVersao` (histórico) — campos sensíveis em `BYTEA` |
| `backend/app/db/migrations/versions/e782fdd01295_*.py` / `c3a19f2d7b64_*.py` | Migração das duas tabelas + coluna `estilo_perfil_encrypted` (Fase 3) |
| `backend/app/schemas/elaboracao.py` | `ElaboracaoPublicSchema`, `VersaoMinutaPublicSchema`, `SugestaoPecaSchema`, `EstiloTextoSchema` — nunca expõem `*_encrypted` |
| `backend/app/services/elaboracao_prompt.py` | Monta o "pacote" do ADR-016 (ficha real do `Processo` + peça + fatos extras + `estilo_perfil`) |
| `backend/app/services/elaboracao_pecas.py` | Catálogo de peças (id/nome/palavras-chave) — mesmo catálogo do frontend (`elaboracao.mock.ts`), manter sincronizado manualmente |
| `backend/app/services/llm/base.py` | `LLMProvider` (ABC): `gerar_minuta` / `editar_minuta` / `sugerir_peca` / `extrair_perfil_estilo` |
| `backend/app/services/llm/contexto.py` | `ElaboracaoContexto` / `FichaProcessoContexto` / `SinaisSugestaoPeca` / `SugestaoPeca` — o que chega ao/vem do provider |
| `backend/app/services/llm/stub_provider.py` | Provider sem rede, ativo por padrão (`LLM_PROVIDER=stub`) — sugestão por palavra-chave, perfil de estilo por estatística simples |
| `backend/app/services/llm/anthropic_provider.py` | Provider real via `httpx` (Claude) — pronto, não testado com chave de verdade |
| `backend/app/services/llm/openrouter_provider.py` | Provider OpenRouter (chat completions). Padrão de teste: `qwen/qwen3.8-27b:free` quando `LLM_MODEL` está vazio |
| `backend/app/services/llm/factory.py` | `get_llm_provider()` escolhe pela config (`stub`, `anthropic`, `openrouter`) |
| `backend/app/services/elaboracao.py` | Ownership, cifra em memória, orquestra o provider e grava versão/estilo/sugestão |
| `backend/app/api/elaboracao.py` | Rotas `/elaboracoes/*` |
| `backend/tests/test_elaboracao.py` | Stub (unitário), ownership e fluxo completo (integração via Postgres) |
| `frontend/src/features/elaboracao/elaboracao.api.ts` / `elaboracao.types.ts` / `elaboracao.constants.ts` | Chamadas tipadas + query keys |
| `frontend/src/features/elaboracao/useElaboracao.ts` | TanStack Query: sessão + versões + mutations (fatos, gerar, editar, estilo) + `useSugestaoPeca` |
| `frontend/src/features/elaboracao/elaboracao.sanitize.ts` | `sanitizarHtmlMinuta` (DOMPurify) — todo HTML do backend passa por aqui antes do editor |
| `frontend/src/features/elaboracao/FatosExtrasPanel.tsx` | Textarea de fatos/teses extras (painel esquerdo) |
| `frontend/src/features/elaboracao/SeletorPeca.tsx` | Seletor de peça — livre; mostra "Sugerido por IA" + explicação só quando há sugestão real para a peça selecionada |
| `frontend/src/features/elaboracao/SeletorPecaEspecifica.tsx` | Upload/paste de modelo (TXT/PDF/DOCX); só o texto (TXT/colar) tem botão "Aplicar estilo" — PDF/DOCX ficam só anexados |
| `frontend/src/features/elaboracao/EditorChatBar.tsx` | Um único botão: "Elaborar" com o chat vazio, "Enviar" quando há texto digitado (aplica a instrução na minuta atual) |
| `frontend/src/features/elaboracao/GrifoSelecaoPanel.tsx` | Executa edição só no trecho selecionado |
| `frontend/src/features/elaboracao/HistoricoVersoes.tsx` / `RightPanel.tsx` | Lista as versões do servidor (mais recente primeiro); "Restaurar" troca o conteúdo exibido |
| `frontend/src/features/elaboracao/ElaboracaoPage.tsx` | Orquestra `useElaboracao`/`useSugestaoPeca`, pré-seleciona peça sugerida (URL ou fallback), sincroniza nova versão → editor |
| `frontend/src/features/processos/ProcessoCabecalho.tsx` | Card "Ação sugerida" sem chamada ao modelo; o link "Elaborar" abre a tela, que sugere a peça uma vez |
| `frontend/src/routes/elaboracao.$processoId.tsx` | `validateSearch` (Zod) para o param opcional `peca` |
| `frontend/src/features/elaboracao/elaboracao.versoes.ts` | Módulo antigo do `localStorage` — mantido (testado isoladamente), mas não é mais a fonte de verdade da tela |

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| POST | `/elaboracoes` | Get-or-create por `{processo_id, peca}`. `peca` tem de ser um id de `PECAS_IDS_VALIDOS` (422 fora do catálogo). 404 se o processo não é do usuário | Bearer |
| GET | `/elaboracoes/sugestao-peca?processo_id=` | Sugestão de peça (Fase 1) a partir da intimação/movimentação mais recente. `peca=null` = sem sinal suficiente (não é erro). 404 se o processo não é do usuário. Rate limit `30/hour` | Bearer |
| PATCH | `/elaboracoes/{id}` | Atualiza `fatos_extras` (`null`/vazio apaga). 404 se a elaboração não é do usuário | Bearer |
| POST | `/elaboracoes/{id}/gerar` | Primeiro rascunho — monta o pacote (incluindo `estilo_perfil`, se houver) e chama o provider. Rate limit `30/hour` | Bearer |
| POST | `/elaboracoes/{id}/editar` | Chat (`trecho_selecionado` ausente) ou grifo (presente). **409** se ainda não há versão, ou se a última não decripta (a listagem dessa versão vem com HTML vazio). Rate limit `30/hour` | Bearer |
| POST | `/elaboracoes/{id}/estilo` | Fase 3 — recebe `{texto}` (TXT/colar), chama `extrair_perfil_estilo` e grava `estilo_perfil_encrypted`. Rate limit `30/hour` (mesmo orçamento de `gerar`/`editar`) | Bearer |
| GET | `/elaboracoes/{id}/versoes` | Lista, mais recente primeiro | Bearer |

> Rotas protegidas usam `Depends(get_current_user)`. `user_id` nunca vem do cliente.
> Elaboração/processo de outro usuário: **404**, não 403.
> Resposta nunca inclui `fatos_extras_encrypted`, `instrucao_encrypted`, `trecho_alvo_encrypted`, `conteudo_encrypted` ou `estilo_perfil_encrypted`.

---

## Padrões seguidos neste módulo

- **Adapter de LLM:** `LLMProvider` isola o resto do produto do provedor ativo. `LLM_PROVIDER=stub` (padrão, sem rede), `anthropic` (exige `ANTHROPIC_API_KEY`) ou `openrouter` (exige `OPENROUTER_API_KEY`) — `get_llm_provider()` decide, nunca um `if` espalhado pela feature. `sugerir_peca`/`extrair_perfil_estilo` seguem o mesmo contrato.
- **Ownership:** toda consulta filtra `Elaboracao.user_id == current_user.id` no banco; criar sessão/sugerir peça exige que o `Processo` seja do usuário.
- **Cifra:** `fatos_extras`, `estilo_perfil`, `instrucao`, `trecho_selecionado` e `conteudo` (minuta) são `BYTEA` cifrados com `encrypt_secret`/`decrypt_secret` (AES-256-GCM) — descriptografados só em memória, na função que os usa.
- **Catálogo de peças validado:** `sugerir_peca_para_processo` só devolve um id presente em `PECAS_IDS_VALIDOS` (`elaboracao_pecas.py`) — sugestão do provider fora do catálogo é tratada como "sem sugestão", nunca propagada ao frontend.
- **Nunca inventar jurisprudência:** tanto o `StubLLMProvider` quanto o system prompt do `AnthropicProvider` são explícitos sobre isso (ADR-016 §3).
- **Teto de tokens:** `LLM_MAX_OUTPUT_TOKENS` (padrão 4000) — nunca gerar sem limite.
- **Sanitização:** `sanitizarHtmlMinuta` (DOMPurify, allowlist de tags) antes de qualquer `editor.commands.setContent(...)` com HTML vindo do backend.
- **Versão sempre nova:** gerar/editar nunca sobrescreve — cada chamada cria uma linha em `elaboracao_versoes`; "Restaurar" só troca o que está exibido, não cria versão nova.

---

## Modelo de dados

```python
class Elaboracao(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "elaboracoes"
    __table_args__ = (UniqueConstraint("user_id", "processo_id", "peca"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    processo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processos.id", ondelete="CASCADE"), index=True)
    peca: Mapped[str] = mapped_column(String(100))
    fatos_extras_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    estilo_perfil_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)  # Fase 3


class ElaboracaoVersao(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "elaboracao_versoes"

    elaboracao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("elaboracoes.id", ondelete="CASCADE"), index=True)
    origem: Mapped[str] = mapped_column(String(20))  # geracao | chat | grifo
    instrucao_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    trecho_alvo_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    conteudo_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(30))
    llm_model: Mapped[str | None] = mapped_column(Text)
```

---

## Settings novas (`backend/app/core/config.py`)

| Variável | Padrão | Uso |
|---|---|---|
| `LLM_PROVIDER` | `stub` | `stub` (sem rede), `anthropic` ou `openrouter` |
| `LLM_MODEL` | vazio | Slug do modelo. Vazio no OpenRouter usa `qwen/qwen3.8-27b:free` |
| `ANTHROPIC_API_KEY` | vazio | Só necessária com `LLM_PROVIDER=anthropic` — nunca hardcoded |
| `OPENROUTER_API_KEY` | vazio | Chave da conta em [openrouter.ai/keys](https://openrouter.ai/keys). Não é por modelo. Nunca `VITE_*` |
| `LLM_MAX_OUTPUT_TOKENS` | `4000` | Teto de tokens de saída |

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| `auth` | `current_user` de toda rota — nenhuma rota aceita `user_id` do cliente |
| `processos` | Ficha (`Processo`) é a fonte do pacote enviado ao LLM — nunca chama e-SAJ/Playwright/DataJud daqui |

---

## O que NÃO fazer aqui

- ❌ Chamar o provedor de LLM do frontend, ou colocar `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` em `VITE_*`.
- ❌ Mandar autos reais (CNJ, partes, fatos do cliente, modelo do escritório) para rota `:free` do OpenRouter — o provedor dessa rota pode treinar no prompt. Texto inventado no teste; modelo pago com política de não treinar quando for processo de verdade.
- ❌ Retornar `fatos_extras_encrypted`/`estilo_perfil_encrypted`/`instrucao_encrypted`/`trecho_alvo_encrypted`/`conteudo_encrypted` em qualquer schema de resposta.
- ❌ Descriptografar fatos/estilo/instrução/minuta fora do momento do uso, ou guardar em atributo de classe/cache.
- ❌ Inserir HTML do backend no editor sem passar por `sanitizarHtmlMinuta`.
- ❌ Deixar o `StubLLMProvider` ou o `AnthropicProvider` citarem jurisprudência real — nenhum dos dois tem essa fonte (ADR-016 §3); ambos são instruídos a nunca inventar.
- ❌ Chamar `gerar`/`editar`/`estilo`/`sugestao-peca` sem rate limit — custo real quando um provedor pago estiver ligado.
- ❌ Assumir que existe versão anterior legível no `editar`: sem versão, ou com blob que não decripta, a rota responde **409** e não chama o modelo.
- ❌ Devolver ao frontend um id de peça sugerida fora do catálogo (`PECAS_IDS_VALIDOS`) — trate como "sem sugestão". O `POST /elaboracoes` também recusa (`422`) um id fora do catálogo.
- ❌ Extrair texto de PDF/DOCX no backend nesta fase — ainda não há parsing binário; só TXT/colar alimentam `extrair_perfil_estilo` (decisão explícita, ver ADR-016).
- ❌ Usar modelo `:free` fora de `development`, ou com ficha real — o OpenRouter recusa o sufixo `:free` antes do HTTP quando `APP_ENV` não é development. Em development o aviso fica no log, só com o nome do modelo.
- ❌ Sobrescrever a peça escolhida manualmente pelo advogado com a sugestão — a pré-seleção só acontece antes da primeira troca manual (ver `sugestaoAplicadaRef` em `ElaboracaoPage.tsx`).

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-09-21 | Implementação inicial (Fases 2 e 4 do ADR-016): adapter de LLM (`stub` + skeleton `anthropic`), tabelas `elaboracoes`/`elaboracao_versoes`, endpoints `/elaboracoes/*`, fiação do frontend (fatos extras, Elaborar, chat, grifo) e migração do histórico de versões do `localStorage` para o servidor |
| 2026-09-21 | Botão único no chat: com o campo vazio ele "Elabora" (primeiro rascunho/novo rascunho), com texto digitado ele "Envia" a instrução como edição — sem adicionar um segundo botão (`EditorChatBar.tsx`) |
| 2026-09-22 | Fases 1 e 3 do ADR-016: `LLMProvider.sugerir_peca`/`extrair_perfil_estilo` (+ `elaboracao_pecas.py`), coluna `estilo_perfil_encrypted`, endpoints `GET /elaboracoes/sugestao-peca` e `POST /elaboracoes/{id}/estilo`, card "Ação sugerida" no cabeçalho do processo (com `?peca=` na navegação), pré-seleção do seletor de peça e botão "Aplicar estilo" no upload de modelo (texto apenas — PDF/DOCX seguem sem extração) |
| 2026-09-29 | Provider `openrouter` (`OPENROUTER_API_KEY`). Sem `LLM_MODEL`, o teste usa `qwen/qwen3.8-27b:free`. O prompt de gerar passa a incluir o perfil de estilo |
| 2026-09-29 | 429 do provedor na sugestão de peça vira "sem sugestão" e pausa novas sugestões automáticas por 10 minutos. Elaborar, chat e grifo devolvem HTTP 429 (a tela avisa, sem nova tentativa automática) |
| 2026-09-30 | OpenRouter pede `reasoning.effort=none` para o Qwen não gastar a saída no raciocínio. O cabeçalho do processo deixa de chamar `sugestao-peca`; a sugestão fica na tela de elaboração |
| 2026-10-01 | Documentado que `openrouter` envia a ficha real. Modelo `:free` permanece só para teste (ADR-016) |
| 2026-10-01 | Modelo OpenRouter `:free` é recusado fora de development (503, sem HTTP). Versão ilegível lista HTML vazio e editar devolve 409. `GET /elaboracoes/sugestao-peca` entra na cota `30/hour` |

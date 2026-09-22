# ADR-016: IA da elaboração via API (LLM no backend), copiloto da minuta, sem RAG jurídico nacional no v1

**Data:** 2026-09-18
**Status:** Aceito (decisão de produto/arquitetura; **implementação ainda não começou**)

Preços e nomes de modelo abaixo são um **retrato em 2026-09-18**. Conferir as páginas oficiais na hora de ligar a chave — mudam com frequência.

---

## Contexto

A tela `/elaboracao/$processoId` já tem seletor de peça (rótulo “Sugerido por IA”), ficha do e-SAJ, upload de peça-modelo, chat, botão Elaborar, grifo de seleção, painel de jurisprudência ilustrativa e versões no `localStorage`. Nada disso chama um modelo: o upload **não** vai ao servidor, Elaborar está desabilitado, o grifo é visual.

O PRD listava “templates de resposta com IA” como pós-MVP. Antes de implementar, ficou definido o que a IA **é** (copiloto daquela elaboração) e o que **não** é (cérebro jurídico nacional, busca sozinha no STJ, análise de vídeo).

Este ADR congela esse recorte, o modo de uso (API, não treino próprio), onde a IA entra na UI, e a comparação Gemini / GPT / Claude / DeepSeek para produção e para **teste barato**.

---

## Decisão

### 1. Como a IA entra no produto

A elaboração é um **pacote** montado no FastAPI e enviado a um LLM. O React **nunca** leva a chave nem chama o provedor.

```
ficha e-SAJ (já no banco)
+ peça escolhida no select (ou a sugerida, se o advogado aceitar)
+ fatos extras que ele digitou (cliente, tese, o que não pode ir ao texto)
+ estilo extraído do modelo de peça desta elaboração
+ anexos: nomes +, se for imagem, descrição da visão (o advogado confere)
+ jurisprudência que ELE marcou ou colou
→ minuta no TipTap (rascunho). Ele sempre edita. Ninguém protocola sozinho.
```

**Não** é um RAG de “todo o direito brasileiro”. Fatos do processo vão em **JSON** (capa, polos, intimação, movimentações). RAG, se existir, é **só** na biblioteca de peças **daquele** `user_id`, quando o chat pedir “usa a preliminar da peça X”.

### 2. Onde a IA é usada (mapa da tela)

| Superfície (já existe o visual) | Papel da IA | v1 |
|---|---|---|
| Seletor de peça | Sugere **uma** peça a partir da intimação/movimento + explicação curta. O select **continua livre** | Sim |
| Peça-modelo (upload) | Extrai texto (DOCX/PDF/TXT) → **perfil de estilo** (JSON) desta elaboração | Sim (1 arquivo já muda o tom; biblioteca permanente depois) |
| Fatos / dados do cliente | Não é modelo: é input humano. Entra no prompt. O e-SAJ não tem tese nem “o que o cliente disse” | Sim (campo novo) |
| **Elaborar** | Primeiro rascunho da minuta | Sim |
| Chat (barra de baixo) | Conversa para **editar** o documento já gerado (“deixe a preliminar mais objetiva”) | Sim |
| Highlight / grifo | Mesmo motor do chat, alvo = **só o trecho selecionado** | Sim |
| Imagens do processo | Visão: descreve o que vê. Texto cita “Doc. N”. Binário vira **anexo** no DOCX/PDF | Sim (descrição + anexo; inserir JPEG no corpo do Word é montagem de arquivo, fase seguinte) |
| Vídeo | **Sem** análise. Só anexo no documento gerado | Sim (arquivo). Sem transcrição/frames |
| Jurisprudência | Usa **somente** o que o advogado marcou ou colou. Opcional: sugerir **termos** para ele buscar no SCON/STF | v1 = cola/marca. Busca automática só com API **licenciada** de acórdãos (não DataJud) |
| Export Word/PDF | Não é LLM: monta arquivo (python-docx ou similar) com minuta + lista de anexos | Depois do rascunho estável |

Chat e grifo são **duas portas** do mesmo endpoint de edição (minuta atual + seleção opcional + instrução + estilo/fatos da sessão). Cada resposta vira versão **no servidor** (o `localStorage` atual não serve quando houver IA).

### 3. O que a IA **não** faz

- Analisar vídeo.
- “Validar prova” no sentido jurídico — organiza o que o advogado anexou; quem assina é ele.
- Buscar jurisprudência **navegando na internet** ou “lembrando” ementa. Modelos **inventam** julgado. DataJud **não** devolve ementa pesquisável por tese (ADR-015: capa/andamento).
- Fine-tune / treinar modelo no acervo do escritório no v1.
- Rodar no browser ou com chave `VITE_*`.
- Mandar ao LLM: CPF, senha, cookie e-SAJ, token OAuth2, pasta digital inteira.
- Travar o Uvicorn do Playwright com geração longa sem teto de tokens; no médio prazo, fila/worker separado.

### 4. Como chamamos o modelo (arquitetura)

- Cliente LLM **atrás** do FastAPI (`httpx` ou SDK oficial), stream para o editor.
- `LLM_PROVIDER` + `LLM_MODEL` + chave em variável de ambiente (`pydantic-settings`). Troca de fornecedor **não** espalha `if openai` na feature.
- Ownership: toda elaboração, chunk e anexo com `user_id = current_user.id`.
- Peças, perfil de estilo e fatos extras **cifrados** em disco (mesmo espírito AES-256 das credenciais). Log sem trecho de autos.
- Rate limit no endpoint de gerar (custo e abuso).
- Provedor de produção: contrato de API **sem** treinar no dado do cliente (Anthropic API e OpenAI API pagas, no modo padrão; Gemini **pago** com “não usar para melhorar produtos” — o **free** do Gemini **usa** o conteúdo para melhorar produtos Google, então **proibido** para autos reais).

### 5. Modelo padrão (produção)

**Padrão: Anthropic Claude Sonnet 5** (texto + imagem na mesma API), via `https://platform.claude.com`.

Motivo: redação longa em português, seguir instrução na minuta, visão para fotos de prova, política de API alinhada a dado de cliente. Haiku 4.5 fica como opção **barata** para sugestão de peça e grifos curtos, se a qualidade no eval interno aguentar.

O adapter permite cair para GPT (OpenAI) ou Gemini **pago** sem redesenhar o produto. DeepSeek não é padrão de produção (ver alternativas).

### 6. Fases de implementação (não ligar tudo no primeiro PR)

1. Sugerir peça + select livre.  
2. Campo de fatos + Elaborar (ficha + tipo + chat curto), sem upload.  
3. Upload do modelo → perfil de estilo.  
4. Chat + grifo sobre a minuta.  
5. Imagens (visão + anexos) e vídeo só como arquivo.  
6. Jurisprudência: seleção/cola; busca automática só com fonte licenciada.

---

## Comparação de provedores (API, 2026-09-18)

Valores em **USD por 1 milhão de tokens**. “Free” abaixo é **API de desenvolvedor**, não o chat do site (ChatGPT grátis ≠ API).

| | **Claude (Anthropic)** | **GPT (OpenAI)** | **Gemini (Google)** | **DeepSeek** |
|---|---|---|---|---|
| Modelo de referência | Sonnet 5; Haiku 4.5 para barato | GPT-4.1 / família GPT-5.x; mini para barato | 2.5 Pro / 2.5 Flash (há 3.x Flash/Pro em preview) | `deepseek-flash` / `deepseek-v4-pro` |
| Input / output (faixa) | Sonnet 5: **$2 / $10**. Haiku 4.5: **$1 / $5** | GPT-4.1: **$2 / $8**. GPT-4o mini: **$0,15 / $0,60** | Flash pago: **$0,30 / $2,50**. Pro pago: **$1,25 / $10** (prompt ≤ 200k) | Flash: da ordem de **$0,14 / $0,28** (barato; confirmar [docs](https://api-docs.deepseek.com/quick_start/pricing)) |
| Visão (foto de prova) | Sim | Sim (4o / 4.1) | Sim | Flash-vision legado aposentado; não assumir visão estável no v1 |
| PT-BR jurídico / minuta longa | Forte (padrão da casa) | Forte | Bom; Flash é mais “rápido/barato” que “peça caprichada” | Barato; qualidade e residência de dado a validar |
| Dado do cliente na API | API **não** treina no input (padrão) | API paga no modo padrão **não** usa para treino; **não** aderir a incentivo de “data sharing” | **Pago:** não usa para melhorar produtos. **Free:** **sim, usa** — vetado para processo real | Empresa fora do Brasil; DPA/LGPD a revisar antes de autos reais |
| Melhor uso aqui | **Produção** (Elaborar + chat) | Alternativa de produção; mini para grifo | **Teste grátis** (só sintético) e, pago, Flash para tarefa curta | Teste barato de texto; não padrão prod |

Ordem de custo aproximado (minuta média): DeepSeek Flash ≪ Gemini Flash pago ≈ GPT mini < Haiku < Sonnet 5 ≈ GPT-4.1 < Gemini Pro / GPT “full”.

### Teste **sem** (ou quase sem) custo

Autos **reais** (CNJ, partes, teses, fotos de prova) **não** entram em tier gratuito que treina no prompt.

1. **Melhor free de verdade para brincar com a API:** [Google AI Studio](https://aistudio.google.com/) / Gemini Developer API, modelo **Flash**, chave em `https://aistudio.google.com/apikey`. Sem cartão no free; cota diária limitada. **Só** petição fictícia / lorem jurídico. No free, o Google pode usar o conteúdo para melhorar produtos.  
2. **Anthropic:** contas novas ganham **crédito pequeno** (valor **não** publicado). Console: [platform.claude.com](https://platform.claude.com). Serve para 1–2 Elaborar de teste; depois é pré-pago.  
3. **DeepSeek:** relatos de **~5 milhões de tokens** em conta nova (~30 dias), [platform.deepseek.com](https://platform.deepseek.com). Confirmar no painel — o grant muda. Bom para estresse de prompt **sem** dado de cliente.  
4. **OpenAI API:** na prática **paga desde o primeiro call** na maior parte das contas novas (o trial de US$ 5 saiu). ChatGPT Free **não** substitui. Playground exige billing.  
5. **Gemini pago vs free:** ligar faturamento no AI Studio **sai** do modo “melhora produtos”, mas **deixa de ser grátis**.

Fluxo sugerido para o Igor: (a) Gemini Flash + textos inventados para sentir o prompt; (b) 1 peça de mentira no Claude com o crédito de signup, se existir; (c) produção com Claude Sonnet + chave no Railway, **nunca** `VITE_*`.

---

## Alternativas consideradas

- **Fine-tune / LoRA no estilo do escritório:** descartado no v1 (volume, custo, vazamento). Perfil JSON extraído das peças dele resolve o “fazer igual”.
- **RAG nacional de lei/jurisprudência:** descartado. Não há API oficial do STJ/STF de ementa (SCON e portal STF são HTML). LexML é metadado. DataJud não é tese. Scraping Google/STJ + “o modelo busca na web” gera julgado falso e ToS frágil.
- **API comercial de acórdãos (Jusbrasil enterprise, etc.):** fica para **depois**, se houver contrato; aí sim o painel lista candidatos **com link**, o advogado marca, a IA só usa o marcado.
- **Modelo 100% local (Llama no Railway):** qualidade e GPU. Pode ser oferta futura para quem não quer dado em API dos EUA; não é o v1.
- **Gemini free em produção:** descartado (treino/melhoria de produto no prompt).
- **Um agente com dezenas de tools** (abrir e-SAJ, DataJud, web): descartado no v1. Um gerador com contexto fixo + edição conversacional.

---

## Consequências

- A UI atual continua válida: o que falta é backend + ligar os botões, na ordem das fases.
- Versões da minuta e peça-modelo passam a ser **dado do servidor** (hoje são só browser) quando a IA ligar — senão o F5 e outro dispositivo perdem o trabalho, e o modelo não vê o estilo.
- Export com anexos (incluindo vídeo) é pipeline de arquivo, não “o LLM desenhou o Word”.
- Jurisprudência ilustrativa do mock **não** vira fonte oficial; o aviso amarelo permanece até haver cola/marca do advogado ou API licenciada.
- Custo por Elaborar em Sonnet 5 é da ordem de **centavos a poucos dólares** por peça grande (depende do tamanho do contexto). Rate limit e teto de tokens são obrigatórios.
- Módulo HTTP/documentação de implementação só nasce quando o primeiro endpoint existir; até lá este ADR é a fonte da decisão.

---

## Referências oficiais (preço / chave)

- Anthropic: [pricing](https://platform.claude.com/docs/en/about-claude/pricing), [API key](https://platform.claude.com/docs/en/get-api-key)
- OpenAI: [models/pricing](https://developers.openai.com/api/docs/models/gpt-4.1)
- Google Gemini: [pricing](https://ai.google.dev/gemini-api/docs/pricing), [billing / free](https://ai.google.dev/gemini-api/docs/billing)
- DeepSeek: [API](https://api-docs.deepseek.com/), console em platform.deepseek.com

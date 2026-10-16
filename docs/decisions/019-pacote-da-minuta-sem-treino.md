# ADR-019: Pacote da minuta sem treino, sem fine-tune e sem RAG

**Data:** 2026-10-06
**Status:** Aceito (decisão de produto; **implementação ainda não começou**)

Complementa o ADR-016. Aquele ADR escolhe o modelo (Claude Sonnet via API, só no backend) e o que a IA não faz. Este descreve **como** uma minuta sai estruturada sem treinar o modelo e sem encher a janela de contexto.

---

## Contexto

O select da elaboração já lista os tipos de peça (`modelosPeca` em `frontend/src/features/elaboracao/elaboracao.mock.ts`): contestação, réplica, recurso inominado, apelação, agravo interno, memoriais, petição inicial, tutela de urgência, impugnação à contestação, embargos de declaração. A ficha já extrai capa e endereçamento (`extrairDadosElaboracao` e `montarEnderecamento` em `elaboracao.processo.ts`). O corpo jurídico ainda não é gerado.

Um modelo base, sozinho, não produz peça decente só com os nomes das partes. Fine-tune ou RAG em banco de modelos e de jurisprudência foi a alternativa cogitada para “ensinar” a estrutura. Os dois foram recusados: fine-tune não guarda fato consultável, pode vazar peça de um cliente no texto de outro e continua inventando julgado; RAG nacional não tem fonte licenciada (ADR-016). “Treino básico” do modelo base também não entra — o peso do modelo fica como o fornecedor entregou.

O risco real de contexto é outro: mandar a pasta digital inteira (todos os PDFs, todas as movimentações) junto com um acervo de modelos. Uma peça mediana, montada como abaixo, fica na casa de 15 a 30 mil tokens. A pasta crua é que estoura a janela e o custo.

---

## Decisão

Cada Elaborar é uma chamada ao modelo base com seis blocos. Nenhum bloco altera o modelo. O backend monta o pacote; o React não chama o provedor e não vê a chave.

### 1. Instrução fixa

Texto nosso, igual em toda geração. Define o papel (minuta para o advogado revisar; ninguém protocola sozinho) e as proibições:

- Não inventar fato, número de processo, data, valor, nome de parte ou julgado.
- Dado ausente no pacote aparece como falta — não é completado.
- Jurisprudência só entra se estiver no pacote (colada ou marcada pelo advogado).

Quando uma minuta sair torta, mexe neste texto ou no esqueleto. Não mexe no modelo.

### 2. Esqueleto do tipo escolhido

Um molde por `id` do select. Não é peça pronta copiada de banco. É a ordem das seções e o que cada uma precisa usar dos fatos.

Exemplos do que o molde precisa fixar:

- **Contestação:** endereçamento, qualificação, síntese da inicial, preliminares só se houver fato que as sustente, impugnação dos fatos narrados, mérito, pedidos, fecho.
- **Embargos de declaração:** vício (omissão, contradição ou obscuridade), trecho da decisão, pedido de integração.

Começar por um tipo só — contestação, ou manifestação sobre intimação. Os outros ids do select entram um a um, quando o primeiro estiver estável. Dez moldes cobrem o select atual.

### 3. Capa do processo

O JSON de `extrairDadosElaboracao` (CNJ, polos, foro/tribunal, valor, juiz, assunto, classe, local) mais o endereçamento de `montarEnderecamento`. Curto de propósito.

### 4. Documento alvo

O texto da intimação, da decisão ou da petição da outra parte — o documento a que a peça responde. Sem ele, a minuta vira formulário com os nomes das partes. A pasta digital inteira não entra.

PDF longo é resumido na ingestão e o Elaborar lê o resumo. Se a pasta for enorme, um modelo barato monta esse dossiê e o modelo forte só escreve a minuta em cima dele. Movimentações entram como linha do tempo curta (data + uma frase), não como HTML de cada andamento.

### 5. Fatos do advogado

Tese, pedido principal, o que não pode aparecer, documentos que ele quer citados. O e-SAJ não tem isso. Sem este campo, a minuta descreve o processo e não defende ninguém.

### 6. Estilo, só se houver arquivo

O upload (DOCX/PDF/TXT) vira perfil curto: tamanho de parágrafo, como abre, como pede, tom. Sem upload, vale o esqueleto do tipo. A peça inteira do usuário não vai no prompt. Perfil, fatos e minuta ficam cifrados no servidor (ADR-016); hoje o upload e as versões ainda estão só no browser.

### Jurisprudência

Só o que o advogado colou ou marcou. Fora isso, a instrução manda não citar julgado. O painel ilustrativo (`JULGADOS_ILUSTRATIVOS`) não é fonte. DataJud não devolve ementa.

### O que “bom” significa

Rascunho que o advogado corrige em minutos. Chat e grifo são o mesmo endpoint de edição em cima da minuta já gerada (“encurte a preliminar”, “reescreva só este parágrafo”). Cada resposta vira versão no servidor. A primeira geração não precisa sair pronta.

### Ordem para implementar

1. Instrução fixa + esqueleto de um tipo.
2. Endpoint que junta capa, documento alvo, texto do advogado e esse esqueleto, e devolve o rascunho ao TipTap.
3. Casos fictícios para julgar: a peça tem as seções do esqueleto; não inventou parte; não citou julgado que não estava no pacote; usou número e foro da capa. Falha ajusta esqueleto ou instrução.
4. Campo de fatos / tese na tela.
5. Upload virando perfil de estilo.
6. Chat e grifo.
7. Os outros esqueletos do select.

Autos reais não entram em API gratuita que usa o prompt para treinar (ADR-016). Rate limit e teto de tokens no endpoint continuam obrigatórios.

### Ordem de grandeza do pacote

| Bloco | Tokens |
|---|---|
| Instrução + esqueleto do tipo | 2–4 mil |
| Capa | 1–2 mil |
| Documento alvo | 2–8 mil |
| Linha do tempo resumida | 1–3 mil |
| Perfil de estilo ou um exemplo curto | 1–4 mil |
| Fatos do advogado | ~1 mil |
| Minuta gerada | 3–8 mil |

Soma típica: 15–30 mil tokens. CPF, senha, cookie do e-SAJ e token OAuth2 não entram no pacote.

---

## Alternativas consideradas

- **Fine-tune ou LoRA no acervo de modelos e jurisprudência:** descartado. Não torna o julgado consultável, aumenta citação falsa convincente, vaza dado entre clientes e prende o estilo a um fornecedor. Já recusado no ADR-016; este ADR confirma que banco de peças público também não entra em treino (direito autoral e, quando o processo é real, dado de parte).
- **“Treino básico” do modelo base:** descartado. Não há etapa de treino. A instrução e o esqueleto são texto enviado em cada chamada.
- **RAG do direito brasileiro:** descartado no v1 (ADR-016). Busca futura, se existir, é na biblioteca de peças **daquele** usuário, quando o chat pedir um trecho — um pedaço, não o acervo.
- **Colar a pasta digital inteira no prompt:** descartado. Estoura contexto e custo, e a minuta piora.

---

## Consequências

- Quem for implementar a elaboração lê este ADR junto com o ADR-016. O 016 continua valendo para provedor, mapa da tela, fases e o que a IA não faz. O contrato do pacote é este.
- O primeiro entregável é um esqueleto e um endpoint, não um modelo próprio.
- Qualidade se mede nos casos fictícios. Ajuste é no texto do pacote.
- Documentação de módulo (`/docs/modulos/`) da elaboração só nasce quando o primeiro endpoint existir.

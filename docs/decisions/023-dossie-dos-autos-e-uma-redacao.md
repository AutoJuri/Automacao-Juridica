# ADR-023: Dossiê dos autos e uma redação

**Data:** 2026-10-20
**Status:** Aceito. A leitura sob demanda e o dossiê cifrado estão no código (ADR-024, 2026-10-21). O advogado confirma o roteiro na tela de preparar a peça (ADR-025, 2026-10-28). A tese sugerida pelo modelo, a redação por capítulo e a jurisprudência automática continuam fora.

Complementa o ADR-016 e o ADR-019. Aqueles escolhem o provedor, o que a IA não faz e os blocos do pacote. Este fecha a ordem: quem lê a pasta, quem escreve a peça, e o que fica para uma versão futura.

---

## Contexto

Um único prompt de “especialista em direito” em cima do PDF cru estoura contexto, custo e qualidade. Um pipeline com um agente por etapa (teses, capítulo, jurisprudência, conferência) multiplica chamada antes de o rascunho único estar estável.

A pasta do processo, porém, precisa entrar na preparação. Sem uma leitura dos autos, a minuta vira formulário com os nomes da capa. O ADR-019 já previa um modelo barato montando o dossiê e o modelo forte só escrevendo. Faltava cravar como essa leitura acontece e o que não se constrói agora.

---

## Decisão

### Redação: uma chamada

O modelo forte recebe o pacote do ADR-019 já pronto e devolve o rascunho inteiro de uma vez. Essa chamada é o Elaborar. Chat e grifo continuam sendo edição dessa minuta, não uma nova geração do zero.

Entram no pacote: instrução fixa, esqueleto do tipo de peça, capa, dossiê, fatos que o advogado digitou e, se houver upload, o perfil curto de estilo. A pasta crua não entra.

### Preparação: um modelo menor, arquivo por arquivo

Antes do Elaborar, um modelo mais barato lê os autos e entrega um dossiê curto. Ele não engole todos os PDFs numa tacada.

1. Cada arquivo é lido à parte. Se a página já tem texto, usa o texto. O carimbo do e-SAJ não conta. OCR só na página escaneada, que no portal costuma trazer só esse carimbo.
2. Cada arquivo vira uma ficha curta: o que é, quem pede o quê, datas e valores.
3. As fichas viram um resumo só. É esse resumo que o redator vê, junto com a linha do tempo curta das movimentações (data + uma frase).

CPF, senha, cookie do e-SAJ e token OAuth2 não entram em nenhuma das duas chamadas.

### O que fica para quando o rascunho único estiver estável

Estas rodadas não entram na primeira construção. Cada uma é outra chamada, outro custo e outro ponto de falha:

- o modelo propor teses e o advogado aprovar o roteiro antes de redigir
- escrever capítulo por capítulo
- conferir citação por citação numa passagem automática separada

O critério do rascunho único continua o do ADR-019: a peça tem as seções do esqueleto, não inventou parte, não citou julgado que não estava no pacote, usou número e foro da capa.

### Jurisprudência automática: versão futura

Não se constrói agora. Até existir uma base licenciada de acórdãos, a citação só entra se o advogado colou ou marcou. O painel ilustrativo da tela não é fonte. DataJud não devolve ementa. Busca na web e “memória” do modelo continuam proibidas (ADR-016).

Quando essa versão existir, a busca é por tese, em base verificada, e a conferência tira ou marca a citação que não bater com o trecho guardado. A única busca aceita antes disso é na biblioteca de peças daquele usuário, quando o chat pedir um trecho — um pedaço, não o acervo.

---

## Alternativas consideradas

- **Um agente só, com a pasta inteira no prompt:** descartado. Estoura a janela e a minuta piora (ADR-019).
- **Um agente por capítulo, tese e citação desde o início:** descartado para o v1. Só vale depois que o rascunho de uma chamada estiver estável.
- **OCR de todos os PDFs numa única chamada do modelo menor:** descartado. O limite de contexto vale para ele também. A leitura é arquivo por arquivo; OCR só onde não há texto.

---

## Consequências

- A ordem de construção segue o ADR-019 (esqueleto de um tipo, pacote, casos fictícios, fatos, estilo, chat) e encaixa o dossiê como a preparação do documento alvo. Sem o resumo, o Elaborar não recebe a pasta crua no lugar.
- Jurisprudência automática permanece documentada e fora do escopo até uma versão futura.
- Quem for implementar lê este ADR junto com o ADR-016 e o ADR-019. O 016 continua valendo para provedor e para o que a IA não faz. O 019 continua valendo para os blocos do pacote.

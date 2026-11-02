# ADR-024: Leitura dos autos em memória

**Data:** 2026-10-21
**Status:** Aceito (implementado)

Complementa o ADR-023. Aquele define a ordem (dossiê, depois uma redação). Este define como o PDF entra: baixa em memória, na hora em que o advogado pede, e só a ficha cifrada fica no banco.

---

## Contexto

O CPO já guarda, em cada movimentação, se há documento e a URL `abrirDocumentoVinculadoMovimentacao.do` (https, host `esaj.tjsp.jus.br`). O link `#liberarAutoPorSenha` fica com `url_documento` nulo. Até aqui a regra era não baixar esse PDF: o advogado abria o e-SAJ no próprio navegador.

Sem o texto, o Elaborar só vê a capa. O ADR-023 pede um dossiê curto antes da redação. Guardar o PDF, ou devolvê-lo ao navegador, exporia a pasta digital fora do portal.

O contrato autenticado (PDF direto ou um salto para a pasta digital) não foi medido nesta entrega com cookie real. Sem sessão, o mesmo endereço responde HTML de acesso negado. O script `backend/scripts/sondar_documento_esaj.py` registra só status, content-type, tamanho, redirecionamento e se o corpo começa com `%PDF`. Não grava o arquivo.

---

## Decisão

A leitura é sob demanda. O botão "Ler autos" dispara uma tarefa dentro do FastAPI. O ciclo de 10 minutos do scheduler não baixa PDF.

1. O cookie da sessão do e-SAJ é descriptografado só dentro da tarefa, num cliente httpx novo, e descartado ao terminar.
2. Cada URL é conferida de novo antes do GET. O corpo é lido em streaming, com teto de tamanho. Vale o binário que começa com `%PDF`, ou um único salto para `/pastadigital/getPDF.do` ou `/pastadigital/abrirDocumentoEdt.do` no mesmo host.
3. Página com texto útil usa a camada de texto (PyMuPDF). O carimbo do e-SAJ ("Para conferir o original" / "cópia do original" / "fls.") é descartado e não conta como texto. Página que só tem esse carimbo, ou que não tem texto, vai para o Tesseract em português, em thread, com semáforo. Há teto de páginas e de páginas com OCR. Estourou: lê o que der e marca `parcial`.
4. Um modelo barato (`LLM_MODEL_DOSSIE`) faz a ficha. O texto do PDF entra entre delimitadores, como dado. Modelo com `:free` continua recusado fora de development.
5. No banco ficam a ficha e o resumo, em `BYTEA`, cifrados com AES-256-GCM. Não há coluna de texto bruto nem de PDF. A URL em claro não é gravada: só o SHA-256, para saber se o documento mudou.
6. A API devolve status, progresso, título, data e o resumo. Não devolve ficha de outro usuário, URL com parâmetros nem o arquivo.
7. Documento sem URL (senha dos autos) entra como `sem_acesso` e fica fora do dossiê. Não pedimos nem guardamos essa senha.
8. 429 do portal para o lote, marca a sessão `bloqueado` com o backoff já existente e não apaga o cookie. Sessão inválida marca `reauth_pendente`, anula o cookie e a tela manda reconectar. A tarefa não faz login sozinha.
9. 429 do provedor de IA deixa o restante `pendente` para retomar. Um documento com erro não derruba os outros.
10. O Elaborar inclui o resumo e uma linha do tempo curta (data + uma frase). Sem dossiê, a minuta segue como antes e o pacote diz que a pasta não foi lida.

Quem pode ler é o dono do processo (`WHERE user_id`). Recurso de outra pessoa é 404. Uma leitura por processo por vez; teto de inícios por usuário. A rota de início também tem limite por IP.

---

## Consequências

- A frase "não baixar o PDF" deixa de valer por inteiro. Continua valendo: não persistir o binário e não fazer proxy para o navegador. O ícone da movimentação ainda abre o e-SAJ no browser do advogado.
- O container precisa de `tesseract-ocr` e `tesseract-ocr-por`. No Windows local, o executável do Tesseract com o idioma `por` precisa estar instalado; a API que roda fora do Docker não herda o pacote da imagem. OCR de manuscrito pode falhar; a ficha marca trecho ilegível em vez de completar.
- O provedor de IA recebe trechos dos autos. Em produção, o modelo tem de ser um que não use esses dados para treino.
- Autos sob segredo de justiça ou com senha ficam de fora. A tela avisa.
- Visualizador interno, guardar o PDF no Drive, leitura no ciclo de 10 minutos, jurisprudência automática, tese aprovada e redação por capítulo continuam fora (ADR-023).

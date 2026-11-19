# ADR-027: PDF da movimentação visto dentro da plataforma

**Data:** 2026-11-09
**Status:** Aceito (implementado; contrato do portal medido com sessão real em 2026-11-09)

Muda uma frase do ADR-024. Aquele dizia "não fazer proxy para o navegador". Este permite, só para o PDF de uma movimentação, com os limites abaixo. O binário continua sem ser gravado.

---

## Contexto

O botão "Visualizar PDF" da movimentação mostrava o texto coletado do CPO e um link para o e-SAJ. O advogado queria ver o documento de verdade, sem sair da plataforma.

O browser do advogado não tem a sessão que o servidor guarda, e o cookie do e-SAJ nunca vai para o frontend. A única forma de mostrar o arquivo é o servidor buscar e entregar os bytes. O ADR-024 já baixa esse mesmo PDF em memória para ler os autos.

---

## Decisão

1. `GET /processos/{processo_id}/movimentacoes/{movimentacao_id}/documento` baixa o PDF em memória, com `baixar_documento` (o mesmo cliente do ADR-024), e responde `application/pdf`. A URL gravada na coleta não abre o arquivo: o e-SAJ responde HTML de acesso inválido. O servidor reabre a ficha CPO, busca o link vivo do mesmo `cdDocumento` e segue o visualizador (`abrirDocumentoEdt.do` → `getPDF.do` na árvore `requestScope`). A query não é logada.
2. A consulta exige `Processo.user_id == usuário do JWT` e a movimentação daquele processo. Outro usuário, ou movimentação sem URL pública do e-SAJ, é 404. O arquivo só sai para o dono.
3. O cookie é descriptografado dentro do serviço, num cliente httpx novo, e descartado. Não sai na resposta nem em log. A query da URL (`cdDocumento`) não é logada.
4. A resposta leva `Cache-Control: no-store, private`. Nada é gravado em disco nem no banco.
5. Erros sem detalhe do portal: 404 sem documento, 409 sessão do e-SAJ indisponível (reconectar), 429 portal limitando, 422 sem PDF ou acima do teto de 15 MB, 502 portal fora do ar. O 429 desta abertura não marca a sessão `bloqueado`: a coleta de 10 minutos continua. Sessão inválida não apaga o cookie.
6. Limite de 60/hora por IP, porque cada abertura é uma ida ao e-SAJ com a sessão do advogado.
7. No frontend, o PDF chega como `Blob` e vira um `blob:` da própria aba, num `<iframe>`. O modal só é montado aberto e a query tem `gcTime: 0`: ao fechar, o `blob:` é revogado e o arquivo sai da memória. Nada vai para `localStorage` nem `sessionStorage`.
8. Sem URL direta (senha dos autos, `#liberarAutoPorSenha`) ou sem sessão, o modal volta ao texto da movimentação e ao link "Abrir no e-SAJ". A consulta pública não tem processo salvo e não usa a rota.

---

## Consequências

- A frase do ADR-024 "não fazer proxy para o navegador" vale agora só para a pasta digital inteira e para o cookie. O PDF de uma movimentação passa pelo servidor, em memória, rumo ao dono.
- Medido em 2026-11-09 com sessão real: a URL gravada na coleta devolve HTML de acesso inválido. O link vivo, depois da ficha, abre o visualizador da pasta e o PDF sai de `getPDF.do`. Se o portal não entregar `%PDF`, o usuário vê 422 e o texto.
- Cada abertura reabre a ficha e pagina no máximo 8 páginas do AJAX das movimentações. Documento mais antigo que isso fica em 422. O 429 do e-SAJ nesta rota não marca a sessão `bloqueado`.
- O browser do advogado passa a ter o PDF em memória enquanto o modal está aberto. Baixar PDF salva o arquivo no computador dele, por escolha dele.
- Continuam fora: guardar o PDF, cache de arquivo no servidor, baixar todas as peças da pasta para o navegador e visualizador para a consulta pública.

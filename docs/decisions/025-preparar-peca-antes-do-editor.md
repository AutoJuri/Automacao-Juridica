# ADR-025: Preparar a peça antes do editor

**Data:** 2026-10-28
**Status:** Aceito

Complementa o ADR-023 e o ADR-024. A leitura dos autos continua em memória. O que muda é onde o advogado vê essa leitura e o que ele confirma antes da minuta.

---

## Contexto

O bloco Autos na ficha de Gerenciais ocupava a tela do processo. O atalho Elaborar abria o editor sem uma etapa visível para conferir o resumo, acrescentar o que os autos não trouxeram ou colar jurisprudência. O ADR-023 deixava o roteiro aprovado para uma versão futura, quando o modelo passasse a propor teses. O advogado já quer essa conferência agora, escrita por ele, sem uma chamada extra de IA.

---

## Decisão

A ficha do processo e os cartões de Elaborações mostram só a barra de progresso dos autos. O botão Preparar peça abre `/preparar/$processoId`.

Nessa tela as etapas ficam visíveis, na ordem:

1. Ler os autos.
2. Revisar o resumo.
3. Completar o roteiro: tese, pedidos, o que acrescentar e o que não incluir.
4. Jurisprudência, se o advogado quiser colar um trecho.
5. Elaborar a minuta, que abre a escolha da peça e depois o editor.

O roteiro fica cifrado em `processo_dossies.roteiro_encrypted`. A API devolve o texto só para o dono do processo. Ao abrir a minuta, se os fatos extras daquela elaboração ainda estão vazios, o roteiro entra ali, com no máximo 8000 caracteres. Fatos que o advogado já gravou no editor não são substituídos.

A redação continua uma chamada só (ADR-023). O modelo não propõe a tese. Capítulo por capítulo e busca automática de jurisprudência continuam fora.

---

## Alternativas consideradas

- **Manter o bloco Autos na ficha:** descartado. A consulta do processo e a preparação da peça são momentos diferentes.
- **Guardar o roteiro só no navegador:** descartado. A conferência precisa sobreviver ao recarregar e chegar na minuta cifrada.
- **O modelo sugerir a tese antes do editor:** descartado nesta versão. É a rodada que o ADR-023 ainda deixa para depois.

---

## Consequências

- Sem leitura concluída, a etapa 1 permanece a atual até o advogado escrever o resumo na mão.
- A mensagem de falha da IA não entra no campo de resumo. O aviso fica na lista dos autos.
- O esqueleto por tipo de peça continua por fazer (ADR-019). O roteiro chega na minuta pelos fatos extras.

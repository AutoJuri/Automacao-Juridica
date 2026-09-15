# ADR-015: Complemento via DataJud em tabela separada, job diário isolado e resolução de tribunal genérica por número CNJ

**Data:** 2026-09-06
**Status:** Aceito

---

## Contexto

A Etapa 9 do PRD pedia integração com a API pública do DataJud (CNJ) para complementar os dados dos processos, detecção de provedor de e-mail por MX, e cobertura de outros tribunais além do e-SAJ.

Antes de implementar, foi preciso esclarecer um ponto importante com o usuário: a API pública do DataJud **não permite** descobrir todos os processos de um advogado por nome/OAB — ela só responde consultas por número de processo já conhecido, e nunca expõe partes ou advogados (Portaria CNJ nº 160/2020, anonimização de dados pessoais). Ou seja, o DataJud não substitui o e-SAJ como fonte primária, nem permite "puxar a carteira" de um advogado — ele só complementa processos que o sistema já rastreia.

Isso mudou o escopo da etapa: de "cobrir outros tribunais" (cadastro/descoberta de novos processos) para "enriquecer processos já rastreados com uma fonte pública adicional", com a resolução de tribunal genérica preparada para quando o sistema passar a rastrear processos de outros tribunais no futuro.

## Decisão

1. **Tabela separada (`processos_datajud`), nunca sobrescreve `Processo`.** Uma linha 1:1 por processo, com FK `ON DELETE CASCADE`. Os campos que já vêm do e-SAJ (`de_classe`, `de_assunto`, `foro`, `vara`...) continuam intocados — o DataJud é sempre uma seção complementar e somente-leitura na ficha, nunca a fonte de verdade.

2. **Job diário, fora do ciclo de 10 min do e-SAJ.** O DataJud tem defasagem de replicação de dias (não minutos), e é uma chave pública **compartilhada** por qualquer sistema que a use — martelar a cada 10 min não traria dado mais fresco e ainda arriscaria bloqueio/rate limit para todo mundo que usa a mesma chave. `job_datajud_diario` roda 1x/dia (cron, 3h), é um job de **sistema** (itera sobre processos de todos os advogados, não por advogado) e usa lote round-robin pequeno (`DATAJUD_LOTE`) — mesmo espírito do throttle de movimentações do CPO (ADR-012).

3. **Resolução de tribunal genérica pelo número CNJ (`app/core/cnj.py`), não hardcode de TJSP.** `resolver_alias_datajud` parseia o número CNJ (`NNNNNNN-DD.AAAA.J.TR.OOOO`) e mapeia segmento+tribunal para o alias do índice DataJud (`tjsp`, `trf3`, `trt2`, `stj`...). Cobertura hoje: Justiça Estadual (todos os 27 estados/DF), TRFs (1–6), TRTs (1–24) e STF/STJ/TST. Tribunal fora dessa tabela (TREs, Justiça Militar Estadual) devolve `None` — tratado como "ainda não suportado", nunca como erro, e nunca bloqueia o job. Essa escolha deixa o sistema pronto para rastrear processos de outros tribunais no futuro sem precisar tocar no cliente DataJud.

4. **Chave pública compartilhada via variável de ambiente.** Mesmo sendo uma chave pública (documentada na wiki do CNJ), ela vai em `DATAJUD_API_KEY` e nunca é hardcoded — o CNJ já trocou essa chave antes, e tratar como segredo de config evita precisar de um deploy de código quando isso acontecer de novo.

## Alternativas consideradas

- **Hardcode de um único alias TJSP:** mais simples, mas o alias já muda por tribunal mesmo hoje (a Justiça Estadual sozinha tem 27 aliases diferentes por UF) — nem teria simplificado, só teria feito o próximo tribunal exigir reescrever o cliente do zero.
- **Job no mesmo ciclo de 10 min dos pipes e-SAJ:** descartado — o DataJud não muda em minutos, e aumentaria sem necessidade a carga sobre uma chave pública compartilhada.
- **DataJud como fonte de descoberta de processos (por OAB):** não é possível com a API pública (não expõe partes/advogados) — descartado nesta etapa; cadastro manual de processo de outro tribunal também ficou fora de escopo.
- **Sobrescrever campos do `Processo` com dado do DataJud quando o e-SAJ estiver vazio:** descartado — misturar as duas fontes na mesma coluna tornaria impossível saber de onde veio cada dado, e o e-SAJ é sempre mais atual para o que ele cobre.

## Consequências

- Adicionar um novo tribunal ao rastreamento (fora do e-SAJ) no futuro só precisa de uma nova entrada no dicionário de alias, não de um novo cliente DataJud.
- A ficha do processo ganha uma seção "Dados públicos (DataJud)" que pode ficar vazia por dias após um processo novo entrar no sistema — é esperado, não é bug.
- O job diário nunca é a fonte principal de atualização — se o DataJud cair ou trocar a chave, o e-SAJ continua funcionando normalmente (isolamento total entre os dois pipelines).

"""Schema do payload extraído do HTML do CPO (`cpopg/show.do`).

Diferente de `esaj_raw.py` (JSON de `tarefas-adv`), aqui a "validação" já
aconteceu no parser (`app.services.esaj_cpo_parser`) — o HTML não tem
contrato estrito, então o parser descarta linha malformada antes de chegar
aqui. Ver ADR-012, ADR-013 e `docs/modulos/esaj-apis.md` seção 5.

Campos de capa que o JSON já traz (`de_classe`, `de_assunto`) não entram
aqui — o CPO só completa o que a API de processos não entrega.
"""

from pydantic import BaseModel, ConfigDict


class MovimentacaoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Sempre "dd/mm/aaaa" (sem hora) — formato de `td.dataMovimentacao` no
    # CPO, diferente do ISO sem-offset das APIs JSON de `tarefas-adv`.
    data: str
    # Primeira linha de texto de `td.descricaoMovimentacao` (ex.: "Certidão
    # de Publicação Expedida"). Pode repetir no início de `descricao`.
    titulo: str | None = None
    # Texto completo da célula (título + detalhe em itálico, se houver).
    descricao: str
    # True quando a célula tem `a.linkMovVincProc` ("Visualizar documento
    # em inteiro teor"). Não significa que o PDF está no nosso servidor.
    tem_documento: bool = False
    # Só URL https do e-SAJ para `abrirDocumentoVinculadoMovimentacao.do`.
    # `#liberarAutoPorSenha` não vira URL (pede senha dos autos — ADR-012).
    url_documento: str | None = None


class CapaCpoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    foro: str | None = None
    vara: str | None = None
    juiz: str | None = None
    distribuicao: str | None = None
    controle: str | None = None
    area: str | None = None
    valor_acao: str | None = None


class ParteCpoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    papel: str
    nome: str | None = None
    advogados: str | None = None


class PeticaoDiversaRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: str
    tipo: str
    protocolo: str | None = None
    # Texto extra da linha (além de data/tipo) — entra no hash de dedupe
    # quando não há protocolo e o tipo se repete no mesmo dia.
    texto_extra: str = ""


class AudienciaCpoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: str
    titulo: str
    situacao: str | None = None
    qt_pessoas: str | None = None


class CpoDetalheRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # True quando a ficha não trouxe a tabela de movimentações nem o botão
    # que as carrega sob demanda (segredo de justiça ou sem vínculo pleno —
    # ver ADR-012). Nunca preenchido a partir de senha/autos.
    requer_senha_processo: bool = False
    # A ficha tem `#btnExibirMovimentacoes`: as linhas vêm de
    # `carregarMovimentacoesAjax.do`, não deste HTML. O pipe completa
    # antes de persistir. Não sai na API.
    movimentacoes_sob_demanda: bool = False
    # Cursor opaco da paginação keyset, quando a primeira página já veio
    # no HTML. Só vive na memória do ciclo — não é persistido nem logado.
    cursor_movimentacoes: str | None = None
    movimentacoes: list[MovimentacaoRaw] = []
    capa: CapaCpoRaw | None = None
    partes: list[ParteCpoRaw] = []
    peticoes: list[PeticaoDiversaRaw] = []
    audiencias_cpo: list[AudienciaCpoRaw] = []
    # True só quando o marcador de empty state do portal está no HTML.
    sem_incidentes: bool = False
    sem_apensos: bool = False

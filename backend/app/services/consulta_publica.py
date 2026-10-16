"""Monta a resposta da consulta pública. Não fala com o banco nem com o Google."""

from datetime import UTC, datetime

from app.schemas.consulta_publica import ConsultaPublicaSchema, MovimentoConsultaPublicaSchema
from app.schemas.processo import DatajudAssuntoPublicSchema
from app.services.datajud import ExibicaoDatajud

MOVIMENTOS_EXIBIDOS = 100


def _instante(valor: datetime | None) -> float:
    if valor is None:
        return 0
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=UTC)
    return valor.timestamp()


def montar_consulta_publica(numero: str, exibicao: ExibicaoDatajud) -> ConsultaPublicaSchema:
    processo = exibicao.processo
    if exibicao.situacao != "encontrado" or processo is None:
        situacao = exibicao.situacao
        if situacao not in ("ausente", "indisponivel", "tribunal_nao_suportado"):
            raise ValueError(situacao)
        return ConsultaPublicaSchema(
            numero=numero.strip(),
            tribunal=exibicao.tribunal,
            situacao=situacao,
        )

    movimentos = sorted(processo.movimentos, key=lambda item: _instante(item.data_hora), reverse=True)
    return ConsultaPublicaSchema(
        numero=numero.strip(),
        tribunal=exibicao.tribunal,
        situacao="encontrado",
        classe_nome=processo.classe.nome if processo.classe else None,
        assuntos=[
            DatajudAssuntoPublicSchema(codigo=assunto.codigo, nome=assunto.nome)
            for assunto in processo.assuntos
        ],
        orgao_julgador=processo.orgao_julgador.nome if processo.orgao_julgador else None,
        data_ajuizamento=processo.data_ajuizamento,
        grau=processo.grau,
        formato=processo.formato.nome if processo.formato else None,
        sistema=processo.sistema.nome if processo.sistema else None,
        atualizado_em=processo.data_hora_ultima_atualizacao,
        sigilo=_rotulo_sigilo(processo.nivel_sigilo),
        movimentos_total=len(movimentos),
        movimentos=[_movimento_publico(item) for item in movimentos[:MOVIMENTOS_EXIBIDOS]],
    )


def _rotulo_sigilo(nivel: int | None) -> str | None:
    if nivel is None:
        return None
    if nivel == 0:
        return "Público"
    return f"Nível {nivel}"


def _movimento_publico(item) -> MovimentoConsultaPublicaSchema:
    complementos = []
    for complemento in item.complementos_tabelados:
        texto = (complemento.nome or "").strip()
        if texto and texto not in complementos:
            complementos.append(texto)
    orgao = item.orgao_julgador.nome if item.orgao_julgador else None
    return MovimentoConsultaPublicaSchema(
        codigo=item.codigo,
        nome=item.nome,
        data_hora=item.data_hora,
        orgao_julgador=orgao,
        complementos=complementos,
    )

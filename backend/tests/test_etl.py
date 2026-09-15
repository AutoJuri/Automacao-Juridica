"""Testes de app.etl.etl — normalização pura, sem banco nem rede."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.etl.etl import (
    TIMEZONE_SP,
    audiencia_cpo_para_campos,
    audiencia_para_campos,
    capa_cpo_para_campos,
    intimacao_para_campos,
    montar_id_esaj_audiencia,
    movimentacao_para_campos,
    parse_data_movimentacao_cpo,
    parse_datetime_esaj,
    peticao_identidade_hash,
    peticao_para_campos,
    processo_para_campos,
)
from app.schemas.esaj_cpo_raw import (
    AudienciaCpoRaw,
    CapaCpoRaw,
    MovimentacaoRaw,
    PeticaoDiversaRaw,
)
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw, ProcessoRaw


class TestParseDatetimeEsaj:
    def test_string_sem_offset_e_localizada_em_sao_paulo(self):
        resultado = parse_datetime_esaj("2026-06-30T11:14:06")

        assert resultado == datetime(2026, 6, 30, 11, 14, 6, tzinfo=TIMEZONE_SP)
        assert resultado.tzinfo is not None

    def test_string_com_offset_preserva_o_offset(self):
        resultado = parse_datetime_esaj("2026-06-30T11:14:06-03:00")

        assert resultado.utcoffset() == timedelta(hours=-3)

    def test_valor_none_retorna_none(self):
        assert parse_datetime_esaj(None) is None

    def test_string_vazia_retorna_none(self):
        assert parse_datetime_esaj("") is None


class TestMontarIdEsajAudiencia:
    def test_formato_composto_estavel(self):
        data = datetime(2026, 7, 21, 16, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

        resultado = montar_id_esaj_audiencia("1A0000XXXX0000", data, "Instrução, Debates e Julgamento")

        assert resultado == (
            "cdProcesso=1A0000XXXX0000|dataAudiencia=2026-07-21T16:00:00-03:00|"
            "titulo=Instrução, Debates e Julgamento"
        )

    def test_data_none_e_titulo_none_nao_quebram(self):
        resultado = montar_id_esaj_audiencia("1A0000XXXX0000", None, None)

        assert resultado == "cdProcesso=1A0000XXXX0000|dataAudiencia=|titulo="

    def test_mesma_entrada_gera_sempre_o_mesmo_id(self):
        data = datetime(2026, 7, 21, 16, 0, 0, tzinfo=UTC)

        primeiro = montar_id_esaj_audiencia("cd1", data, "Audiência")
        segundo = montar_id_esaj_audiencia("cd1", data, "Audiência")

        assert primeiro == segundo

    def test_titulo_longo_trunca_id_em_255_e_permanece_deterministico(self):
        from app.etl.etl import ID_ESAJ_MAX

        data = datetime(2026, 7, 21, 16, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        titulo = "A" * 400

        primeiro = montar_id_esaj_audiencia("1A0000XXXX0000", data, titulo)
        segundo = montar_id_esaj_audiencia("1A0000XXXX0000", data, titulo)

        assert len(primeiro) == ID_ESAJ_MAX
        assert primeiro == segundo
        assert primeiro.startswith("cdProcesso=1A0000XXXX0000|dataAudiencia=")
        assert "|titulo=" in primeiro
        assert primeiro.endswith("A")


class TestIntimacaoParaCampos:
    def test_mapeia_todos_os_campos(self):
        raw = IntimacaoRaw.model_validate(
            {
                "id": "cdProcesso=1A0,nuSeqIntimacao=10,oab=123456SP",
                "titulo": "Mero expediente",
                "descricao": "Texto da intimação",
                "cdProcesso": "1A0000XXXX0000",
                "instancia": "PG",
                "dataMovimentacao": "2026-06-30T11:14:06",
                "ciencia": False,
            }
        )

        campos = intimacao_para_campos(raw)

        assert campos["id_esaj"] == raw.id
        assert campos["titulo"] == "Mero expediente"
        assert campos["descricao"] == "Texto da intimação"
        assert campos["instancia"] == "PG"
        assert campos["data_movimentacao"] == datetime(2026, 6, 30, 11, 14, 6, tzinfo=TIMEZONE_SP)
        assert campos["ciencia"] is False
        assert "cd_processo" not in campos

    def test_id_esaj_e_titulo_longos_sao_truncados(self):
        from app.etl.etl import ID_ESAJ_MAX, TITULO_MAX

        raw = IntimacaoRaw.model_validate(
            {
                "id": "I" * 400,
                "titulo": "T" * 400,
                "cdProcesso": "1A0000XXXX0000",
            }
        )

        campos = intimacao_para_campos(raw)

        assert len(campos["id_esaj"]) == ID_ESAJ_MAX
        assert len(campos["titulo"]) == TITULO_MAX


class TestAudienciaParaCampos:
    def test_mapeia_todos_os_campos(self):
        raw = AudienciaRaw.model_validate(
            {
                "dataAudiencia": "2026-07-21T16:00:00",
                "titulo": "Instrução, Debates e Julgamento",
                "local": "Sala de Audiências",
                "cdProcesso": "1A0000XXXX0000",
            }
        )

        campos = audiencia_para_campos(raw, "id-composto-de-teste")

        assert campos["id_esaj"] == "id-composto-de-teste"
        assert campos["titulo"] == "Instrução, Debates e Julgamento"
        assert campos["local"] == "Sala de Audiências"
        assert campos["data_audiencia"] == datetime(2026, 7, 21, 16, 0, 0, tzinfo=TIMEZONE_SP)

    def test_titulo_e_local_longos_sao_truncados(self):
        from app.etl.etl import LOCAL_MAX, TITULO_MAX

        raw = AudienciaRaw.model_validate(
            {
                "titulo": "T" * 400,
                "local": "L" * 400,
                "cdProcesso": "1A0000XXXX0000",
            }
        )

        campos = audiencia_para_campos(raw, "id-curto")

        assert len(campos["titulo"]) == TITULO_MAX
        assert len(campos["local"]) == LOCAL_MAX


class TestParseDataMovimentacaoCpo:
    def test_data_dd_mm_aaaa_e_localizada_em_sao_paulo_meia_noite(self):
        resultado = parse_data_movimentacao_cpo("18/08/2026")

        assert resultado == datetime(2026, 8, 18, 0, 0, 0, tzinfo=TIMEZONE_SP)

    def test_valor_none_retorna_none(self):
        assert parse_data_movimentacao_cpo(None) is None

    def test_string_vazia_retorna_none(self):
        assert parse_data_movimentacao_cpo("") is None

    def test_formato_invalido_retorna_none_sem_levantar_excecao(self):
        assert parse_data_movimentacao_cpo("não é uma data") is None
        assert parse_data_movimentacao_cpo("2026-08-18") is None


class TestMovimentacaoParaCampos:
    def test_mapeia_data_titulo_e_descricao(self):
        raw = MovimentacaoRaw(data="18/08/2026", titulo="Certidão de Publicação Expedida", descricao="Certidão de Publicação Expedida\nRelação: 999/2026")

        campos = movimentacao_para_campos(raw)

        assert campos["data_movimentacao"] == datetime(2026, 8, 18, 0, 0, 0, tzinfo=TIMEZONE_SP)
        assert campos["titulo"] == "Certidão de Publicação Expedida"
        assert campos["descricao"] == "Certidão de Publicação Expedida\nRelação: 999/2026"
        assert campos["tem_documento"] is False
        assert campos["url_documento"] is None

    def test_mapeia_documento_quando_url_e_segura(self):
        raw = MovimentacaoRaw(
            data="18/08/2026",
            titulo="Despacho",
            descricao="Despacho",
            tem_documento=True,
            url_documento="https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?cdDocumento=1",
        )

        campos = movimentacao_para_campos(raw)

        assert campos["tem_documento"] is True
        assert campos["url_documento"] == (
            "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?cdDocumento=1"
        )

    def test_descarta_url_documento_que_nao_e_https_do_esaj(self):
        raw = MovimentacaoRaw(
            data="18/08/2026",
            titulo="Despacho",
            descricao="Despacho",
            tem_documento=True,
            url_documento="javascript:alert(1)",
        )

        campos = movimentacao_para_campos(raw)

        assert campos["tem_documento"] is True
        assert campos["url_documento"] is None

    def test_titulo_longo_e_truncado(self):
        from app.etl.etl import TITULO_MAX

        raw = MovimentacaoRaw(data="18/08/2026", titulo="T" * 400, descricao="descrição qualquer")

        campos = movimentacao_para_campos(raw)

        assert len(campos["titulo"]) == TITULO_MAX

    def test_data_invalida_gera_data_movimentacao_none(self):
        raw = MovimentacaoRaw(data="data-invalida", titulo="Título", descricao="descrição qualquer")

        campos = movimentacao_para_campos(raw)

        assert campos["data_movimentacao"] is None


class TestProcessoParaCampos:
    def test_mapeia_partes_como_dict_com_chaves_camelcase(self):
        raw = ProcessoRaw.model_validate(
            {
                "cdProcesso": "1A0000XXXX0000",
                "nuProcesso": "00000000000000000000",
                "deClasse": "Procedimento Comum Cível",
                "deAssunto": "Assunto do processo",
                "instancia": "PG",
                "parteAtiva": {"nome": "Parte Ativa", "representada": True},
                "partePassiva": {"nome": "Parte Passiva", "representada": False},
                "urlCpo": "https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo=1A0000XXXX0000",
                "urlPasta": "https://esaj.tjsp.jus.br/cpopg/abrirPastaDigitalIntegracao.do",
            }
        )

        campos = processo_para_campos(raw)

        assert campos["cd_processo"] == "1A0000XXXX0000"
        assert campos["parte_ativa"] == {"nome": "Parte Ativa", "nomeSocial": None, "representada": True}
        assert campos["parte_passiva"]["nome"] == "Parte Passiva"

    def test_partes_ausentes_viram_none(self):
        raw = ProcessoRaw.model_validate({"cdProcesso": "1A0000XXXX0000"})

        campos = processo_para_campos(raw)

        assert campos["parte_ativa"] is None
        assert campos["parte_passiva"] is None

    def test_url_cpo_de_host_interno_vira_none(self):
        raw = ProcessoRaw.model_validate(
            {
                "cdProcesso": "1A0000XXXX0000",
                "urlCpo": "https://127.0.0.1/cpopg/show.do",
            }
        )

        campos = processo_para_campos(raw)

        assert campos["url_cpo"] is None


class TestCapaCpoParaCampos:
    def test_nao_inclui_classe_nem_assunto(self):
        capa = CapaCpoRaw(foro="Foro Central", vara="1ª Vara", juiz="Fulano", valor_acao="R$ 1,00")
        campos = capa_cpo_para_campos(capa)
        assert campos["foro"] == "Foro Central"
        assert "de_classe" not in campos
        assert "de_assunto" not in campos

    def test_capa_ausente_vira_dict_vazio(self):
        assert capa_cpo_para_campos(None) == {}


class TestPeticaoParaCampos:
    def test_protocolo_define_identidade_independente_do_tipo(self):
        a = PeticaoDiversaRaw(data="03/10/2023", tipo="Petição Intermediária", protocolo="FAKE.1")
        b = PeticaoDiversaRaw(data="04/10/2023", tipo="Outro", protocolo="FAKE.1")
        assert peticao_identidade_hash(a) == peticao_identidade_hash(b)
        campos = peticao_para_campos(a)
        assert campos["protocolo"] == "FAKE.1"
        assert campos["data_peticao"] is not None

    def test_sem_protocolo_tipo_igual_no_mesmo_dia_colapsa(self):
        a = PeticaoDiversaRaw(data="03/10/2023", tipo="Petição Intermediária")
        b = PeticaoDiversaRaw(data="03/10/2023", tipo="Petição Intermediária")
        assert peticao_identidade_hash(a) == peticao_identidade_hash(b)


class TestAudienciaCpoParaCampos:
    def test_mapeia_data_titulo_situacao(self):
        raw = AudienciaCpoRaw(data="25/08/2026", titulo="Instrução", situacao="Realizada", qt_pessoas="3")
        campos = audiencia_cpo_para_campos(raw)
        assert campos["titulo"] == "Instrução"
        assert campos["situacao"] == "Realizada"
        assert campos["qt_pessoas"] == "3"
        assert campos["data_audiencia"] is not None

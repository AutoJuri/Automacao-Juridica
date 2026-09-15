"""Testes de parsing do número CNJ e resolução do alias DataJud."""

from app.core.cnj import extrair_segmento_tribunal, resolver_alias_datajud


class TestExtrairSegmentoTribunal:
    def test_numero_mascarado(self):
        assert extrair_segmento_tribunal("1002345-67.2025.8.26.0100") == ("8", "26")

    def test_numero_sem_mascara(self):
        assert extrair_segmento_tribunal("10023456720258260100") == ("8", "26")

    def test_numero_vazio_e_none(self):
        assert extrair_segmento_tribunal("") is None
        assert extrair_segmento_tribunal(None) is None  # type: ignore[arg-type]

    def test_numero_interno_do_esaj_nao_e_cnj(self):
        # cd_processo do e-SAJ não segue o formato do número CNJ.
        assert extrair_segmento_tribunal("01ABC23") is None


class TestResolverAliasDatajud:
    def test_justica_estadual_tjsp(self):
        assert resolver_alias_datajud("1002345-67.2025.8.26.0100") == "tjsp"

    def test_justica_estadual_tjrj(self):
        assert resolver_alias_datajud("1002345-67.2025.8.19.0100") == "tjrj"

    def test_distrito_federal_usa_tjdft(self):
        assert resolver_alias_datajud("1002345-67.2025.8.07.0100") == "tjdft"

    def test_justica_federal_trf3(self):
        assert resolver_alias_datajud("1002345-67.2025.4.03.6100") == "trf3"

    def test_justica_do_trabalho_trt2(self):
        assert resolver_alias_datajud("1002345-67.2025.5.02.0100") == "trt2"

    def test_justica_do_trabalho_tribunal_90_e_tst(self):
        assert resolver_alias_datajud("1002345-67.2025.5.90.0100") == "tst"

    def test_tribunal_superior_stj(self):
        assert resolver_alias_datajud("1002345-67.2025.3.00.0000") == "stj"

    def test_tribunal_superior_stf(self):
        assert resolver_alias_datajud("1002345-67.2025.1.00.0000") == "stf"

    def test_numero_invalido_devolve_none(self):
        assert resolver_alias_datajud("numero-invalido") is None

    def test_segmento_nao_mapeado_devolve_none(self):
        # Segmento 6 (Justiça Eleitoral) e 9 (Justiça Militar Estadual)
        # ainda não têm alias mapeado — não é erro, só "não suportado".
        assert resolver_alias_datajud("1002345-67.2025.6.26.0100") is None
        assert resolver_alias_datajud("1002345-67.2025.9.13.0100") is None

    def test_tribunal_estadual_desconhecido_devolve_none(self):
        assert resolver_alias_datajud("1002345-67.2025.8.99.0100") is None

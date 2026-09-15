"""Testes de app.services.esaj_cpo_parser — fixtures sintéticas em
tests/fixtures/ (a captura real é gitignorada, ver ADR-012)."""

from pathlib import Path

from app.services.esaj_cpo_parser import parsear_cpo_html, url_cpo_publica

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _carregar(nome: str) -> str:
    return (FIXTURES_DIR / nome).read_text(encoding="utf-8")


class TestParsearCpoHtml:
    def test_extrai_movimentacoes_da_tabela_todas(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        assert resultado.requer_senha_processo is False
        assert len(resultado.movimentacoes) == 4
        # Ordem do HTML é preservada (mais recente primeiro, como o e-SAJ envia).
        assert resultado.movimentacoes[0].data == "18/08/2026"
        assert resultado.movimentacoes[0].titulo == "Certidão de Publicação Expedida"
        assert resultado.movimentacoes[0].tem_documento is False
        assert resultado.movimentacoes[0].url_documento is None

    def test_movimentacao_sem_detalhe_usa_titulo_como_descricao(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        sem_detalhe = resultado.movimentacoes[1]
        assert sem_detalhe.titulo == "Petição Juntada"
        assert sem_detalhe.descricao == "Petição Juntada"

    def test_movimentacao_com_link_de_intimacao_nao_recebida_e_extraida(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        ordinatorio = resultado.movimentacoes[2]
        assert ordinatorio.titulo == "Ato Ordinatório - Intimação - DJE"
        assert "Manifeste-se a parte autora" in ordinatorio.descricao
        assert ordinatorio.tem_documento is True
        assert ordinatorio.url_documento is None

    def test_link_abrir_documento_vira_url_https_do_esaj(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        remetido = resultado.movimentacoes[3]
        assert remetido.tem_documento is True
        assert remetido.url_documento == (
            "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do"
            "?processo.codigo=FAKE0000&cdDocumento=123"
        )

    def test_href_javascript_nao_vira_url_documento(self):
        html = """
        <tbody id="tabelaTodasMovimentacoes">
          <tr class="containerMovimentacao">
            <td class="dataMovimentacao">01/01/2026</td>
            <td class="descricaoMovimentacao">
              <a class="linkMovVincProc" href="javascript:alert(1)"></a>
              Petição Juntada
            </td>
          </tr>
        </tbody>
        """
        resultado = parsear_cpo_html(html)

        assert resultado.movimentacoes[0].tem_documento is True
        assert resultado.movimentacoes[0].url_documento is None

    def test_movimentacao_com_detalhe_multilinha_preserva_texto(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        remetido = resultado.movimentacoes[3]
        assert remetido.titulo == "Remetido ao DJE"
        assert "Teor do ato" in remetido.descricao
        assert "Advogados(s)" in remetido.descricao

    def test_tabela_ultimas_movimentacoes_nao_e_usada_como_fonte(self):
        # A fixture tem 1 linha em tabelaUltimasMovimentacoes e 4 em
        # tabelaTodasMovimentacoes — o parser deve usar só a segunda.
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))
        assert len(resultado.movimentacoes) == 4

    def test_sem_tabela_de_movimentacoes_marca_requer_senha(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample_bloqueado.html"))

        assert resultado.requer_senha_processo is True
        assert resultado.movimentacoes == []

    def test_html_vazio_nao_levanta_excecao(self):
        resultado = parsear_cpo_html("")

        assert resultado.requer_senha_processo is True
        assert resultado.movimentacoes == []

    def test_html_malformado_nao_levanta_excecao(self):
        resultado = parsear_cpo_html("<html><body><div>lixo sem estrutura</div>")

        assert resultado.requer_senha_processo is True
        assert resultado.movimentacoes == []

    def test_linha_sem_data_e_omitida_sem_derrubar_o_parse(self):
        html = """
        <tbody id="tabelaTodasMovimentacoes">
          <tr class="containerMovimentacao">
            <td class="dataMovimentacao"></td>
            <td class="descricaoMovimentacao">Movimentação sem data</td>
          </tr>
          <tr class="containerMovimentacao">
            <td class="dataMovimentacao">01/01/2026</td>
            <td class="descricaoMovimentacao">Movimentação válida</td>
          </tr>
        </tbody>
        """
        resultado = parsear_cpo_html(html)

        assert resultado.requer_senha_processo is False
        assert len(resultado.movimentacoes) == 1
        assert resultado.movimentacoes[0].descricao == "Movimentação válida"


class TestParsearCpoBlocosComplementares:
    def test_extrai_capa_sem_sobrescrever_classe_no_schema(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        assert resultado.capa is not None
        assert resultado.capa.foro == "Foro Central"
        assert resultado.capa.vara == "1ª Vara Cível"
        assert resultado.capa.juiz == "Fulano da Silva"
        assert resultado.capa.distribuicao == "11/09/2023 às 10:18 - Livre"
        assert resultado.capa.controle == "2023/000350"
        assert resultado.capa.area == "Cível"
        assert resultado.capa.valor_acao == "R$ 1.000,00"
        dumped = resultado.capa.model_dump()
        assert "de_classe" not in dumped
        assert "assunto" not in dumped

    def test_partes_vem_da_tabela_completa_nao_da_principal(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        assert [p.papel for p in resultado.partes] == ["Reqte", "Reqdo", "TerIntCer"]
        assert resultado.partes[0].nome == "Parte Ativa Fake"
        assert resultado.partes[0].advogados is not None
        assert "Beltrano" in resultado.partes[0].advogados
        assert resultado.partes[1].advogados is None

    def test_partes_cai_na_tabela_principal_quando_a_completa_nao_existe(self):
        html = """
        <tbody id="tabelaTodasMovimentacoes">
          <tr class="containerMovimentacao">
            <td class="dataMovimentacao">01/01/2026</td>
            <td class="descricaoMovimentacao">Movimentação válida</td>
          </tr>
        </tbody>
        <table id="tablePartesPrincipais">
          <tr class="fundoClaro">
            <td class="label">Reqte</td>
            <td class="nomeParteEAdvogado">Parte Ativa Fake<br/>Advogado: Beltrano (OAB 000000/SP)</td>
          </tr>
          <tr class="fundoEscuro">
            <td class="label">Reqdo</td>
            <td class="nomeParteEAdvogado">Parte Passiva Fake</td>
          </tr>
        </table>
        """
        resultado = parsear_cpo_html(html)

        assert [p.papel for p in resultado.partes] == ["Reqte", "Reqdo"]
        assert resultado.partes[0].nome == "Parte Ativa Fake"
        assert resultado.partes[1].nome == "Parte Passiva Fake"

    def test_peticoes_descarta_cabecalho_e_lê_protocolo(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        assert len(resultado.peticoes) == 2
        assert resultado.peticoes[0].data == "03/10/2023"
        assert resultado.peticoes[0].tipo == "Petição Intermediária"
        assert resultado.peticoes[0].protocolo == "FAKE.23.00000001-0"
        assert resultado.peticoes[1].tipo == "Pedido de Habilitação"
        assert resultado.peticoes[1].protocolo is None

    def test_marcadores_de_vazio_incidentes_apensos_audiencias(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample.html"))

        assert resultado.sem_incidentes is True
        assert resultado.sem_apensos is True
        assert resultado.audiencias_cpo == []

    def test_audiencias_cpo_preenchidas_ignoram_cabecalho(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample_audiencias.html"))

        assert resultado.requer_senha_processo is False
        assert len(resultado.audiencias_cpo) == 2
        primeira = resultado.audiencias_cpo[0]
        assert primeira.data == "25/08/2026"
        assert primeira.titulo == "Instrução"
        assert primeira.situacao == "Realizada"
        assert primeira.qt_pessoas == "3"
        assert resultado.audiencias_cpo[1].qt_pessoas is None
        assert resultado.sem_incidentes is False
        assert resultado.sem_apensos is False

    def test_pagina_bloqueada_nao_preenche_blocos_complementares(self):
        resultado = parsear_cpo_html(_carregar("cpo_sample_bloqueado.html"))

        assert resultado.requer_senha_processo is True
        assert resultado.capa is None
        assert resultado.partes == []
        assert resultado.peticoes == []
        assert resultado.audiencias_cpo == []
        assert resultado.sem_incidentes is False
        assert resultado.sem_apensos is False


class TestUrlCpoPublica:
    def test_aceita_show_do_do_esaj(self):
        url = "https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo=FAKE"
        assert url_cpo_publica(url) == url

    def test_rejeita_javascript(self):
        assert url_cpo_publica("javascript:alert(1)") is None

    def test_rejeita_host_interno(self):
        assert url_cpo_publica("https://127.0.0.1/cpopg/show.do") is None

    def test_rejeita_path_fora_de_cpopg(self):
        assert url_cpo_publica("https://esaj.tjsp.jus.br/tarefas-adv/api/processos") is None

    def test_rejeita_userinfo(self):
        assert url_cpo_publica("https://user:pass@esaj.tjsp.jus.br/cpopg/show.do") is None

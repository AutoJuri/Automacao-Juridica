"""Testes das funções puras de `email_capture` (padrão AAA) — sem rede."""

from datetime import UTC, datetime

from app.services.auth_esaj import LoginEsajError
from app.services.email_capture import (
    DOMINIO_REMETENTE_ESAJ,
    CodigoNaoEncontradoError,
    _gmail_list_params,
    _outlook_list_params,
    eh_email_do_esaj,
    extrair_codigo_verificacao,
)


class TestEhEmailDoEsaj:
    def test_aceita_endereco_puro_do_dominio(self):
        assert eh_email_do_esaj("esaj@tjsp.jus.br") is True

    def test_aceita_formato_nome_e_endereco(self):
        assert eh_email_do_esaj("Portal e-SAJ <esaj@tjsp.jus.br>") is True

    def test_aceita_subdominio_do_tjsp(self):
        assert eh_email_do_esaj("noreply@notificacoes.tjsp.jus.br") is True

    def test_rejeita_dominio_diferente(self):
        assert eh_email_do_esaj("atacante@tjsp.jus.br.malicioso.com") is False

    def test_rejeita_endereco_sem_arroba(self):
        assert eh_email_do_esaj("nao-e-um-email") is False

    def test_case_insensitive(self):
        assert eh_email_do_esaj("ESAJ@TJSP.JUS.BR") is True


class TestExtrairCodigoVerificacao:
    def test_extrai_com_contexto_explicito_plain_text(self):
        texto = "Olá, seu código de verificação é 123456. Não compartilhe."
        assert extrair_codigo_verificacao(texto) == "123456"

    def test_extrai_com_contexto_em_html(self):
        texto = "<html><body><p>Seu <b>código</b> de acesso: <strong>654321</strong></p></body></html>"
        assert extrair_codigo_verificacao(texto) == "654321"

    def test_fallback_para_numero_de_6_digitos_isolado_sem_contexto(self):
        texto = "Prezado usuário, use 987654 para continuar."
        assert extrair_codigo_verificacao(texto) == "987654"

    def test_retorna_none_quando_nao_ha_codigo(self):
        assert extrair_codigo_verificacao("Nenhum código nesta mensagem.") is None

    def test_prefere_trecho_contextual_a_outros_numeros_no_texto(self):
        texto = "Protocolo 2024001 registrado. Seu código de verificação: 111222."
        assert extrair_codigo_verificacao(texto) == "111222"

    def test_ignora_tags_html_ao_extrair(self):
        texto = "<div>codigo:<span>445566</span></div>"
        assert extrair_codigo_verificacao(texto) == "445566"


class TestGmailListParams:
    def test_filtra_remetente_tjsp_e_data_em_epoch(self):
        since = datetime(2026, 8, 17, 20, 0, 0, tzinfo=UTC)

        params = _gmail_list_params(since)

        assert params["q"] == f"from:{DOMINIO_REMETENTE_ESAJ} after:{int(since.timestamp())}"


class TestOutlookListParams:
    def test_lista_sem_body_e_filtra_por_data(self):
        since = datetime(2026, 8, 17, 20, 0, 0, tzinfo=UTC)

        params = _outlook_list_params(since)

        assert params["$select"] == "id,from,receivedDateTime"
        assert "body" not in params["$select"]
        assert params["$filter"] == "receivedDateTime ge 2026-08-17T20:00:00Z"
        assert params["$top"] == "10"


class TestCodigoNaoEncontradoError:
    def test_e_login_esaj_error_com_tipo_codigo_nao_encontrado(self):
        erro = CodigoNaoEncontradoError()

        assert isinstance(erro, LoginEsajError)
        assert erro.tipo == "codigo_nao_encontrado"

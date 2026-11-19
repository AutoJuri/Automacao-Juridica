"""Envio transacional. O SDK do Resend não é chamado."""

import logging

import pytest

from app.services.email_plataforma import (
    entregar,
    mensagem_convite,
    mensagem_redefinicao,
)

TOKEN = "11111111-1111-4111-8111-111111111111"
LINK_SENHA = f"http://localhost:3000/redefinir-senha?token={TOKEN}"
LINK_CONVITE = f"http://localhost:3000/convite/{TOKEN}"


class Ambiente:
    def __init__(
        self,
        *,
        development: bool,
        chave: str = "",
        remetente: str = "AdvogAtiva <noreply@exemplo.com>",
    ) -> None:
        self.is_development = development
        self.resend_api_key = chave
        self.email_from = remetente


def _ambiente(monkeypatch: pytest.MonkeyPatch, ambiente: Ambiente) -> None:
    monkeypatch.setattr("app.services.email_plataforma.get_settings", lambda: ambiente)


class TestMensagens:
    def test_redefinicao_tem_botao_e_o_prazo(self):
        mensagem = mensagem_redefinicao("ana@example.com", LINK_SENHA, 60)
        assert "Redefinir senha" in mensagem.html
        assert "60 minutos" in mensagem.html
        assert "senha atual continua a mesma" in mensagem.html
        assert LINK_SENHA in mensagem.texto

    def test_convite_escapa_html_e_nao_quebra_o_assunto(self):
        mensagem = mensagem_convite(
            "ana@example.com",
            "Silva\n<script>",
            "Advogado",
            LINK_CONVITE,
        )
        assert "<script>" not in mensagem.html
        assert "&lt;script&gt;" in mensagem.html
        assert "Ver convite" in mensagem.html
        assert f'href="{LINK_CONVITE}"' in mensagem.html
        assert "\n" not in mensagem.assunto
        assert mensagem.assunto == "Convite para Silva <script>"


class TestEntrega:
    @pytest.mark.asyncio
    async def test_com_chave_envia_e_nao_loga_o_link(self, monkeypatch, caplog):
        _ambiente(monkeypatch, Ambiente(development=True, chave="re_teste"))
        capturado: dict[str, str] = {}

        def falso(api_key: str, remetente: str, mensagem) -> str:
            capturado["api_key"] = api_key
            capturado["remetente"] = remetente
            capturado["assunto"] = mensagem.assunto
            capturado["destino"] = mensagem.destinatario
            return "email-1"

        monkeypatch.setattr("app.services.email_plataforma._enviar", falso)
        with caplog.at_level(logging.INFO):
            await entregar(mensagem_redefinicao("ana@example.com", LINK_SENHA, 60))

        assert capturado == {
            "api_key": "re_teste",
            "remetente": "AdvogAtiva <noreply@exemplo.com>",
            "assunto": "Redefinir senha da AdvogAtiva",
            "destino": "ana@example.com",
        }
        assert "email-1" in caplog.text
        assert TOKEN not in caplog.text
        assert "re_teste" not in caplog.text
        assert "ana@example.com" not in caplog.text

    @pytest.mark.asyncio
    async def test_sem_chave_em_development_loga_o_link(self, monkeypatch, caplog):
        _ambiente(monkeypatch, Ambiente(development=True))
        with caplog.at_level(logging.WARNING):
            await entregar(mensagem_convite("ana@example.com", "Silva", "Advogado", LINK_CONVITE))

        assert LINK_CONVITE in caplog.text
        assert "ana@example.com" not in caplog.text

    @pytest.mark.asyncio
    async def test_sem_chave_fora_de_development_nao_loga_o_token(self, monkeypatch, caplog):
        _ambiente(monkeypatch, Ambiente(development=False))
        with caplog.at_level(logging.INFO):
            await entregar(mensagem_redefinicao("ana@example.com", LINK_SENHA, 60))

        assert TOKEN not in caplog.text
        assert "redefinir-senha" not in caplog.text
        assert "@" not in caplog.text
        assert "ausente" in caplog.text

    @pytest.mark.asyncio
    async def test_falha_do_provedor_nao_leva_o_link_para_o_log(self, monkeypatch, caplog):
        _ambiente(monkeypatch, Ambiente(development=False, chave="re_teste"))

        def falha(api_key: str, remetente: str, mensagem) -> str:
            raise RuntimeError(f"vazou {TOKEN} ana@example.com")

        monkeypatch.setattr("app.services.email_plataforma._enviar", falha)
        with caplog.at_level(logging.WARNING):
            await entregar(mensagem_redefinicao("ana@example.com", LINK_SENHA, 60))

        assert "RuntimeError" in caplog.text
        assert TOKEN not in caplog.text
        assert "ana@example.com" not in caplog.text

    @pytest.mark.asyncio
    async def test_chave_sem_remetente_nao_loga_o_link(self, monkeypatch, caplog):
        _ambiente(monkeypatch, Ambiente(development=True, chave="re_teste", remetente="  "))
        with caplog.at_level(logging.WARNING):
            await entregar(mensagem_redefinicao("ana@example.com", LINK_SENHA, 60))

        assert TOKEN not in caplog.text
        assert "ausente" in caplog.text

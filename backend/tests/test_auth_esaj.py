"""Testes de `selecionar_cookies_sessao` (padrão AAA) — sem abrir browser."""

import pytest

from app.services.auth_esaj import LoginEsajError, selecionar_cookies_sessao


def _cookie(name: str, value: str, path: str = "/") -> dict:
    return {"name": name, "value": value, "path": path, "domain": "esaj.tjsp.jus.br"}


class TestSelecionarCookiesSessao:
    def test_seleciona_apenas_jsessionid_do_path_tarefas_adv(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-login", path="/sajcas"),
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert resultado["JSESSIONID"] == "sessao-autenticada"
        assert resultado["CASTGC"] == "castgc-valor"

    def test_inclui_cookie_k_jsessionid_dinamico_e_sajcas_url(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
            _cookie("K-JSESSIONID-A1B2C3", "k-valor"),
            _cookie("sajcasUrl", "https://esaj.tjsp.jus.br/sajcas"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert resultado["K-JSESSIONID-A1B2C3"] == "k-valor"
        assert resultado["sajcasUrl"] == "https://esaj.tjsp.jus.br/sajcas"

    def test_ignora_cookies_irrelevantes(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
            _cookie("outro_cookie_qualquer", "valor-irrelevante"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert "outro_cookie_qualquer" not in resultado

    def test_rejeita_quando_falta_jsessionid_do_path_correto(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-login", path="/sajcas"),
            _cookie("CASTGC", "castgc-valor"),
        ]

        with pytest.raises(LoginEsajError) as exc_info:
            selecionar_cookies_sessao(cookies)
        assert exc_info.value.tipo == "portal_indisponivel"

    def test_rejeita_quando_falta_castgc(self):
        cookies = [_cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv")]

        with pytest.raises(LoginEsajError) as exc_info:
            selecionar_cookies_sessao(cookies)
        assert exc_info.value.tipo == "portal_indisponivel"

    def test_rejeita_lista_de_cookies_vazia(self):
        with pytest.raises(LoginEsajError):
            selecionar_cookies_sessao([])

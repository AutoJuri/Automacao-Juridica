"""Testes de `selecionar_cookies_sessao` (padrão AAA) — sem abrir browser."""

import httpx
import pytest

from app.services.auth_esaj import LoginEsajError, selecionar_cookies_sessao
from app.services.esaj_http import (
    absorver_set_cookie,
    cookies_para_caminho,
    montar_client,
    normalizar_cookies,
)


def _cookie(name: str, value: str, path: str = "/") -> dict:
    return {"name": name, "value": value, "path": path, "domain": "esaj.tjsp.jus.br"}


def _valor(cookies: list[dict], nome: str, path: str | None = None) -> str | None:
    for cookie in cookies:
        if cookie["name"] == nome and (path is None or cookie["path"] == path):
            return cookie["value"]
    return None


class TestSelecionarCookiesSessao:
    def test_seleciona_apenas_jsessionid_do_path_tarefas_adv(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-login", path="/sajcas"),
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert _valor(resultado, "JSESSIONID", "/tarefas-adv") == "sessao-autenticada"
        assert _valor(resultado, "JSESSIONID", "/sajcas") is None
        assert _valor(resultado, "CASTGC") == "castgc-valor"

    def test_ignora_jsessionid_de_arquivo_estatico(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("JSESSIONID", "estatico", path="/cpopg/js/jquery"),
            _cookie("JSESSIONID", "ficha", path="/cpopg"),
            _cookie("CASTGC", "castgc-valor"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert _valor(resultado, "JSESSIONID", "/cpopg") == "ficha"
        assert _valor(resultado, "JSESSIONID", "/cpopg/js/jquery") is None

    def test_guarda_sessao_da_ficha_e_da_pasta(self):
        cookies = [
            _cookie("JSESSIONID", "tarefas", path="/tarefas-adv"),
            _cookie("JSESSIONID", "ficha", path="/cpopg"),
            _cookie("JSESSIONID", "pasta", path="/pastadigital"),
            _cookie("CASTGC", "castgc-valor", path="/sajcas"),
        ]

        resultado = selecionar_cookies_sessao(cookies)
        pasta = cookies_para_caminho(normalizar_cookies(resultado), "/pastadigital/getPDF.do")
        cas = cookies_para_caminho(normalizar_cookies(resultado), "/sajcas/login")

        assert _valor(resultado, "JSESSIONID", "/pastadigital") == "pasta"
        assert pasta["JSESSIONID"] == "pasta"
        assert "CASTGC" not in pasta
        assert cas["CASTGC"] == "castgc-valor"

    def test_inclui_cookie_k_jsessionid_dinamico_e_sajcas_url(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
            _cookie("K-JSESSIONID-A1B2C3", "k-valor"),
            _cookie("sajcasUrl", "https://esaj.tjsp.jus.br/sajcas"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert _valor(resultado, "K-JSESSIONID-A1B2C3") == "k-valor"
        assert _valor(resultado, "sajcasUrl") == "https://esaj.tjsp.jus.br/sajcas"

    def test_ignora_cookies_irrelevantes(self):
        cookies = [
            _cookie("JSESSIONID", "sessao-autenticada", path="/tarefas-adv"),
            _cookie("CASTGC", "castgc-valor"),
            _cookie("outro_cookie_qualquer", "valor-irrelevante"),
        ]

        resultado = selecionar_cookies_sessao(cookies)

        assert _valor(resultado, "outro_cookie_qualquer") is None

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

    def test_formato_antigo_ainda_vale_para_qualquer_caminho(self):
        escolhidos = cookies_para_caminho(
            normalizar_cookies({"JSESSIONID": "antiga", "CASTGC": "tgc"}),
            "/cpopg/show.do",
        )

        assert escolhidos["JSESSIONID"] == "antiga"


def test_set_cookie_da_pasta_substitui_o_jsessionid_daquele_path():
    jar = list(normalizar_cookies([{"name": "JSESSIONID", "value": "antiga", "path": "/pastadigital"}]))

    absorver_set_cookie(jar, ["JSESSIONID=nova; Path=/pastadigital"])

    escolhidos = cookies_para_caminho(jar, "/pastadigital/getPDF.do")
    assert escolhidos["JSESSIONID"] == "nova"


@pytest.mark.asyncio
async def test_client_reenvia_o_cookie_que_a_pasta_devolveu():
    vistos: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        vistos.append(request.headers.get("cookie", ""))
        if request.url.path.endswith("abrirPastaProcessoDigital.do"):
            return httpx.Response(
                200,
                text="ok",
                headers={"set-cookie": "JSESSIONID=nova; Path=/pastadigital"},
                request=request,
            )
        return httpx.Response(200, content=b"%PDF", request=request)

    transport = httpx.MockTransport(handler)
    async with montar_client([{"name": "JSESSIONID", "value": "antiga", "path": "/pastadigital"}]) as client:
        client._transport = transport
        await client.get("https://esaj.tjsp.jus.br/pastadigital/abrirPastaProcessoDigital.do")
        await client.get("https://esaj.tjsp.jus.br/pastadigital/getPDF.do")

    assert "JSESSIONID=antiga" in vistos[0]
    assert "JSESSIONID=nova" in vistos[1]

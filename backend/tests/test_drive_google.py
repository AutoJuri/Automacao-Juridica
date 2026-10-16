"""Integração do Drive com o Google. O Google é sempre simulado.

A transação do teste faz rollback. Nenhuma chamada real sai da máquina.
"""

import json
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core import arquivos_drive
from app.core.config import get_settings
from app.core.security import create_oauth_state_token, decrypt_secret
from app.models.drive_arquivo import DriveArquivo
from app.models.drive_conexao import DriveConexao
from app.services import drive_arquivos, oauth_google_drive
from app.services.drive_google import API, UPLOAD, ClienteDrive
from app.services.oauth_common import OAuthTokenExchangeError

SENHA = "SenhaForte123!"
PDF = b"%PDF-1.7\nconteudo de teste"
MIME_PASTA = "application/vnd.google-apps.folder"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _cadastrar(client, *, name: str = "Marina") -> tuple[str, str]:
    resposta = await client.post(
        "/auth/cadastro",
        json={
            "name": name,
            "email": f"pytest-gdrive-{uuid4().hex[:12]}@example.com",
            "password": SENHA,
            "cargo": "advogado",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["access_token"], resposta.json()["user"]["id"]


class GoogleFalso:
    """Faz o papel da API do Drive e guarda cada chamada para os testes olharem."""

    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str, str]] = []
        self.itens: dict[str, dict] = {}
        self.contador = 0
        self.negar_primeira_com_401 = False
        self.parametros: list[dict] = []

    def _id(self, prefixo: str) -> str:
        self.contador += 1
        return f"{prefixo}{self.contador:012d}"

    def cadastrar(self, *, mime: str, nome: str = "externo.pdf", tamanho: str | None = "10",
                  conteudo: bytes = PDF, trashed: bool = False) -> str:
        identificador = self._id("ext")
        self.itens[identificador] = {
            "id": identificador, "name": nome, "mimeType": mime, "size": tamanho,
            "trashed": trashed, "_conteudo": conteudo, "_pais": [],
        }
        return identificador

    def metodos(self, metodo: str) -> list[tuple[str, str, str]]:
        return [chamada for chamada in self.chamadas if chamada[0] == metodo]

    @staticmethod
    def _publico(item: dict) -> dict:
        return {chave: valor for chave, valor in item.items() if not chave.startswith("_")}

    async def responder(self, metodo: str, url: str, token: str, kwargs: dict) -> httpx.Response:
        self.chamadas.append((metodo, url, token))
        params = kwargs.get("params") or {}
        self.parametros.append(params)

        if self.negar_primeira_com_401:
            self.negar_primeira_com_401 = False
            return httpx.Response(401, json={"error": "invalid"})

        if url == UPLOAD and metodo == "POST":
            identificador = self._id("arq")
            corpo = kwargs["content"]
            self.itens[identificador] = {
                "id": identificador, "name": "enviado", "mimeType": "x", "size": str(len(corpo)),
                "trashed": False, "_conteudo": corpo, "_pais": [],
            }
            return httpx.Response(200, json=self._publico(self.itens[identificador]))

        if url == API and metodo == "POST":
            identificador = self._id("pasta")
            self.itens[identificador] = {
                "id": identificador, "name": kwargs["json"]["name"], "mimeType": MIME_PASTA,
                "trashed": False, "_conteudo": b"", "_pais": kwargs["json"].get("parents", []),
            }
            return httpx.Response(200, json={"id": identificador})

        if url.startswith(f"{API}/"):
            identificador = url.removeprefix(f"{API}/")
            item = self.itens.get(identificador)
            if item is None:
                return httpx.Response(404, json={"error": "notFound"})
            if metodo == "GET" and params.get("alt") == "media":
                return httpx.Response(200, content=item["_conteudo"])
            if metodo == "GET":
                return httpx.Response(200, json=self._publico(item))
            if metodo == "PATCH":
                corpo = kwargs.get("json") or {}
                if corpo.get("trashed"):
                    item["trashed"] = True
                if "addParents" in params:
                    item["_pais"] = [params["addParents"]]
                return httpx.Response(200, json={"id": identificador})
        return httpx.Response(500)


@pytest.fixture
def google(monkeypatch) -> GoogleFalso:
    falso = GoogleFalso()

    async def _enviar_falso(self, metodo, url, token, timeout, **kwargs):
        return await falso.responder(metodo, url, token, kwargs)

    monkeypatch.setattr(ClienteDrive, "_enviar", _enviar_falso)

    config = get_settings()
    monkeypatch.setattr(config, "google_client_id", "cliente-teste")
    monkeypatch.setattr(config, "google_client_secret", "segredo-teste")
    monkeypatch.setattr(config, "google_picker_api_key", "chave-teste")
    monkeypatch.setattr(config, "google_project_number", "123456789")
    return falso


def _tokens(**extra) -> dict:
    base = {
        "access_token": "acesso-1",
        "refresh_token": "refresh-1",
        "expires_in": 3600,
        "scope": oauth_google_drive.SCOPE,
    }
    return {**base, **extra}


async def _conectar(db, user_id: str, **extra) -> None:
    await drive_arquivos.salvar_conexao(db, UUID(user_id), _tokens(**extra))


async def _pasta(client, token: str, nome: str = "Contratos") -> dict:
    resposta = await client.post("/drive/pastas", json={"nome": nome}, headers=_auth(token))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _enviar(client, token: str, pasta_id: str, nome: str = "peca.pdf", conteudo: bytes = PDF, **data):
    return client.post(
        f"/drive/pastas/{pasta_id}/arquivos",
        files={"arquivo": (nome, conteudo, "application/octet-stream")},
        data=data,
        headers=_auth(token),
    )


async def _total_fichas(db) -> int:
    return await db.scalar(select(func.count()).select_from(DriveArquivo))


class TestConexao:
    @pytest.mark.asyncio
    async def test_authorize_exige_login_e_configuracao(self, cliente_auth, monkeypatch):
        client, _db = cliente_auth
        assert (await client.get("/drive/google/authorize")).status_code == 401

        token, _ = await _cadastrar(client)
        config = get_settings()
        monkeypatch.setattr(config, "google_client_id", "")
        monkeypatch.setattr(config, "google_client_secret", "")
        assert (await client.get("/drive/google/authorize", headers=_auth(token))).status_code == 503

    @pytest.mark.asyncio
    async def test_authorize_pede_so_drive_file(self, cliente_auth, google):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)
        resposta = await client.get("/drive/google/authorize", headers=_auth(token))
        assert resposta.status_code == 200, resposta.text
        url = resposta.json()["authorize_url"]
        assert "scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.file" in url
        assert "gmail" not in url
        assert "access_type=offline" in url
        assert "%2Fdrive%2Fgoogle%2Fcallback" in url

    @pytest.mark.asyncio
    async def test_callback_recusa_state_ruim_sem_expor_motivo(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        _, user_id = await _cadastrar(client)

        async def _nao_deve_trocar(code):
            raise AssertionError("não pode trocar o code com state inválido")

        monkeypatch.setattr(oauth_google_drive, "exchange_code", _nao_deve_trocar)

        for query in (
            "",
            "?code=abc",
            "?state=abc",
            "?code=abc&state=lixo",
            f"?code=abc&state={create_oauth_state_token(UUID(user_id), 'gmail')}",
        ):
            resposta = await client.get(f"/drive/google/callback{query}", follow_redirects=False)
            assert resposta.status_code == 307, (query, resposta.status_code)
            assert resposta.headers["location"].endswith("/drive?google=erro"), query
        assert await db.scalar(select(func.count()).select_from(DriveConexao)) == 0

    @pytest.mark.asyncio
    async def test_callback_conecta_e_guarda_o_token_criptografado(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)

        async def _trocar(code):
            assert code == "codigo-teste"
            return _tokens(access_token="segredo-de-acesso", refresh_token="segredo-de-refresh")

        monkeypatch.setattr(oauth_google_drive, "exchange_code", _trocar)
        state = create_oauth_state_token(UUID(user_id), oauth_google_drive.STATE_PROVIDER)
        resposta = await client.get(
            f"/drive/google/callback?code=codigo-teste&state={state}", follow_redirects=False
        )
        assert resposta.headers["location"].endswith("/drive?google=conectado")

        conexao = await db.scalar(select(DriveConexao).where(DriveConexao.user_id == UUID(user_id)))
        assert conexao is not None
        assert b"segredo-de-acesso" not in conexao.token_encrypted
        assert b"segredo-de-refresh" not in conexao.token_encrypted
        assert json.loads(decrypt_secret(conexao.token_encrypted))["refresh_token"] == "segredo-de-refresh"

        status_ = await client.get("/drive/google/status", headers=_auth(token))
        assert status_.json() == {"configurado": True, "picker_configurado": True, "conectado": True}
        assert "segredo" not in status_.text

    @pytest.mark.asyncio
    async def test_callback_sem_escopo_ou_com_troca_falha_nao_conecta(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        _, user_id = await _cadastrar(client)
        state = create_oauth_state_token(UUID(user_id), oauth_google_drive.STATE_PROVIDER)

        async def _sem_escopo(code):
            return _tokens(scope="openid email")

        monkeypatch.setattr(oauth_google_drive, "exchange_code", _sem_escopo)
        resposta = await client.get(f"/drive/google/callback?code=x&state={state}", follow_redirects=False)
        assert resposta.headers["location"].endswith("/drive?google=escopo")

        async def _falha(code):
            raise OAuthTokenExchangeError("recusado")

        monkeypatch.setattr(oauth_google_drive, "exchange_code", _falha)
        resposta = await client.get(f"/drive/google/callback?code=x&state={state}", follow_redirects=False)
        assert resposta.headers["location"].endswith("/drive?google=erro")

        async def _sem_refresh(code):
            return _tokens(refresh_token=None)

        monkeypatch.setattr(oauth_google_drive, "exchange_code", _sem_refresh)
        resposta = await client.get(f"/drive/google/callback?code=x&state={state}", follow_redirects=False)
        assert resposta.headers["location"].endswith("/drive?google=erro")
        assert await db.scalar(select(func.count()).select_from(DriveConexao)) == 0

    @pytest.mark.asyncio
    async def test_desconectar_revoga_e_mantem_as_fichas(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)
        assert (await _enviar(client, token, pasta["id"])).status_code == 201

        revogados: list[str] = []

        async def _revogar(valor):
            revogados.append(valor)
            return True

        monkeypatch.setattr(oauth_google_drive, "revoke_token", _revogar)
        resposta = await client.delete("/drive/google", headers=_auth(token))
        assert resposta.status_code == 200
        assert resposta.json()["conectado"] is False
        assert revogados == ["refresh-1"]
        assert await db.scalar(select(func.count()).select_from(DriveConexao)) == 0

        lista = await client.get(f"/drive/pastas/{pasta['id']}/arquivos", headers=_auth(token))
        assert len(lista.json()) == 1
        sem_conexao = await _enviar(client, token, pasta["id"])
        assert sem_conexao.status_code == 409

    @pytest.mark.asyncio
    async def test_picker_token(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)

        sem_conexao = await client.post("/drive/google/picker-token", headers=_auth(token))
        assert sem_conexao.status_code == 409

        await _conectar(db, user_id)
        resposta = await client.post("/drive/google/picker-token", headers=_auth(token))
        assert resposta.status_code == 200, resposta.text
        corpo = resposta.json()
        assert set(corpo) == {"access_token", "expires_in", "api_key", "app_id"}
        assert corpo["access_token"] == "acesso-1"
        assert corpo["api_key"] == "chave-teste"
        assert corpo["app_id"] == "123456789"
        assert 60 <= corpo["expires_in"] <= 3600
        assert resposta.headers["cache-control"] == "no-store"
        assert "refresh" not in resposta.text

        monkeypatch.setattr(get_settings(), "google_picker_api_key", "")
        assert (await client.post("/drive/google/picker-token", headers=_auth(token))).status_code == 503

    @pytest.mark.asyncio
    async def test_picker_renova_token_perto_de_vencer(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id, expires_in=30)

        async def _renovar(refresh):
            assert refresh == "refresh-1"
            return {"access_token": "acesso-2", "expires_in": 3600, "scope": oauth_google_drive.SCOPE}

        monkeypatch.setattr(oauth_google_drive, "refresh_access_token", _renovar)
        resposta = await client.post("/drive/google/picker-token", headers=_auth(token))
        assert resposta.json()["access_token"] == "acesso-2"

        conexao = await db.scalar(select(DriveConexao).where(DriveConexao.user_id == UUID(user_id)))
        guardado = json.loads(decrypt_secret(conexao.token_encrypted))
        assert guardado["access_token"] == "acesso-2"
        assert guardado["refresh_token"] == "refresh-1"  # preservado

    @pytest.mark.asyncio
    async def test_rotas_exigem_login(self, cliente_auth):
        client, _db = cliente_auth
        ficticio = uuid4()
        for metodo, url in (
            ("GET", "/drive/google/status"),
            ("DELETE", "/drive/google"),
            ("POST", "/drive/google/picker-token"),
            ("GET", f"/drive/pastas/{ficticio}/arquivos"),
            ("POST", f"/drive/pastas/{ficticio}/arquivos/vincular"),
            ("GET", f"/drive/arquivos/{ficticio}/conteudo"),
            ("PATCH", f"/drive/arquivos/{ficticio}"),
            ("DELETE", f"/drive/arquivos/{ficticio}"),
        ):
            resposta = await client.request(metodo, url)
            assert resposta.status_code == 401, (metodo, url)


class TestArquivos:
    @pytest.mark.asyncio
    async def test_envio_lista_baixa_move_e_exclui(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        origem = await _pasta(client, token, "Origem")
        destino = await _pasta(client, token, "Destino")

        enviado = await _enviar(client, token, origem["id"], nome="../Petição inicial.pdf")
        assert enviado.status_code == 201, enviado.text
        ficha = enviado.json()
        assert ficha["nome"] == "Petição inicial.pdf"
        assert ficha["mime_type"] == "application/pdf"
        assert ficha["tamanho"] == len(PDF)
        assert ficha["origem"] == "upload"
        assert ficha["ausente_no_google"] is False
        assert ficha["url_drive"].startswith("https://drive.google.com/file/d/")
        assert set(ficha) == {
            "id", "pasta_id", "nome", "mime_type", "tamanho", "origem",
            "ausente_no_google", "url_drive", "created_at",
        }

        # a pasta raiz e a pasta do usuário nascem no Drive, uma vez só
        nomes = [item["name"] for item in google.itens.values() if item["mimeType"] == MIME_PASTA]
        assert nomes == ["AdvogAtiva", "Origem"]
        assert (await _enviar(client, token, origem["id"], nome="outra.pdf")).status_code == 201
        nomes = [item["name"] for item in google.itens.values() if item["mimeType"] == MIME_PASTA]
        assert nomes == ["AdvogAtiva", "Origem"]

        pastas = {p["id"]: p for p in (await client.get("/drive/pastas", headers=_auth(token))).json()}
        assert pastas[origem["id"]]["total_arquivos"] == 2
        assert pastas[destino["id"]]["total_arquivos"] == 0
        assert (await client.get(f"/drive/pastas/{origem['id']}", headers=_auth(token))).json()["total_arquivos"] == 2

        baixado = await client.get(f"/drive/arquivos/{ficha['id']}/conteudo", headers=_auth(token))
        assert baixado.status_code == 200
        assert "attachment" in baixado.headers["content-disposition"]
        assert baixado.headers["x-content-type-options"] == "nosniff"

        movido = await client.patch(
            f"/drive/arquivos/{ficha['id']}", json={"pasta_id": destino["id"]}, headers=_auth(token)
        )
        assert movido.status_code == 200, movido.text
        assert movido.json()["pasta_id"] == destino["id"]
        assert any("addParents" in p and "removeParents" in p for p in google.parametros)
        lista = await client.get(f"/drive/pastas/{destino['id']}/arquivos", headers=_auth(token))
        assert [a["id"] for a in lista.json()] == [ficha["id"]]

        excluido = await client.delete(f"/drive/arquivos/{ficha['id']}", headers=_auth(token))
        assert excluido.status_code == 204
        arquivo_google = [i for i in google.itens.values() if i["mimeType"] == "x"][0]
        assert arquivo_google["trashed"] is True
        assert (await client.get(f"/drive/pastas/{destino['id']}/arquivos", headers=_auth(token))).json() == []

    @pytest.mark.asyncio
    async def test_origem_elaboracao(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)
        resposta = await _enviar(client, token, pasta["id"], origem="elaboracao")
        assert resposta.status_code == 201
        assert resposta.json()["origem"] == "elaboracao"
        assert (await _enviar(client, token, pasta["id"], origem="drive")).status_code == 422

    @pytest.mark.asyncio
    async def test_envio_recusado_antes_de_falar_com_o_google(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)

        for nome, conteudo in (
            ("virus.exe", b"MZ\x90\x00"),
            ("falso.pdf", b"MZ\x90\x00"),
            ("vazio.pdf", b""),
            ("sem-extensao", PDF),
        ):
            resposta = await _enviar(client, token, pasta["id"], nome=nome, conteudo=conteudo)
            assert resposta.status_code == 422, (nome, resposta.status_code)

        monkeypatch.setattr(arquivos_drive, "TAMANHO_MAX", 64)
        monkeypatch.setattr("app.api.drive.TAMANHO_MAX", 64)
        grande = await _enviar(client, token, pasta["id"], conteudo=b"%PDF-" + b"0" * 128)
        assert grande.status_code == 413
        assert google.chamadas == []
        assert await _total_fichas(db) == 0

    @pytest.mark.asyncio
    async def test_envio_sem_conexao_pede_para_conectar(self, cliente_auth, google):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)
        pasta = await _pasta(client, token)
        resposta = await _enviar(client, token, pasta["id"])
        assert resposta.status_code == 409
        assert "Google Drive" in resposta.json()["detail"]
        assert google.chamadas == []

    @pytest.mark.asyncio
    async def test_arquivo_e_pasta_de_outra_pessoa_sao_404(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        outro, outro_id = await _cadastrar(client, name="Ana")
        await _conectar(db, user_id)
        await _conectar(db, outro_id)
        pasta = await _pasta(client, token)
        ficha = (await _enviar(client, token, pasta["id"])).json()
        minha_outra = await _pasta(client, outro, "Da Ana")
        chamadas_antes = len(google.chamadas)

        assert (await client.get(f"/drive/pastas/{pasta['id']}/arquivos", headers=_auth(outro))).status_code == 404
        assert (await _enviar(client, outro, pasta["id"])).status_code == 404
        assert (
            await client.post(
                f"/drive/pastas/{pasta['id']}/arquivos/vincular",
                json={"google_file_id": "a" * 20},
                headers=_auth(outro),
            )
        ).status_code == 404
        assert (await client.get(f"/drive/arquivos/{ficha['id']}/conteudo", headers=_auth(outro))).status_code == 404
        assert (
            await client.patch(
                f"/drive/arquivos/{ficha['id']}", json={"pasta_id": minha_outra["id"]}, headers=_auth(outro)
            )
        ).status_code == 404
        assert (await client.delete(f"/drive/arquivos/{ficha['id']}", headers=_auth(outro))).status_code == 404
        assert len(google.chamadas) == chamadas_antes

        # mover para a pasta de outra pessoa também é 404
        assert (
            await client.patch(
                f"/drive/arquivos/{ficha['id']}", json={"pasta_id": minha_outra["id"]}, headers=_auth(token)
            )
        ).status_code == 404
        intacta = await client.get(f"/drive/pastas/{pasta['id']}/arquivos", headers=_auth(token))
        assert [a["id"] for a in intacta.json()] == [ficha["id"]]

    @pytest.mark.asyncio
    async def test_vincular_so_grava_a_ficha_e_nao_mexe_no_arquivo_da_pessoa(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        origem = await _pasta(client, token, "A")
        destino = await _pasta(client, token, "B")
        externo = google.cadastrar(mime="application/pdf", nome="contrato antigo.pdf", tamanho="2048")

        criado = await client.post(
            f"/drive/pastas/{origem['id']}/arquivos/vincular",
            json={"google_file_id": externo},
            headers=_auth(token),
        )
        assert criado.status_code == 201, criado.text
        ficha = criado.json()
        assert ficha["origem"] == "drive"
        assert ficha["nome"] == "contrato antigo.pdf"
        assert ficha["tamanho"] == 2048
        assert externo not in json.dumps({k: v for k, v in ficha.items() if k != "url_drive"})

        repetido = await client.post(
            f"/drive/pastas/{origem['id']}/arquivos/vincular",
            json={"google_file_id": externo},
            headers=_auth(token),
        )
        assert repetido.status_code == 409

        antes = len(google.chamadas)
        movido = await client.patch(
            f"/drive/arquivos/{ficha['id']}", json={"pasta_id": destino["id"]}, headers=_auth(token)
        )
        assert movido.status_code == 200
        excluido = await client.delete(f"/drive/arquivos/{ficha['id']}", headers=_auth(token))
        assert excluido.status_code == 204
        assert len(google.chamadas) == antes  # nada de PATCH no Drive da pessoa
        assert google.itens[externo]["trashed"] is False

    @pytest.mark.asyncio
    async def test_vincular_recusa_pasta_documento_nativo_lixeira_e_inacessivel(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)

        async def _vincular(identificador: str):
            return await client.post(
                f"/drive/pastas/{pasta['id']}/arquivos/vincular",
                json={"google_file_id": identificador},
                headers=_auth(token),
            )

        assert (await _vincular(google.cadastrar(mime=MIME_PASTA, nome="pasta"))).status_code == 422
        assert (
            await _vincular(google.cadastrar(mime="application/vnd.google-apps.document"))
        ).status_code == 422
        assert (
            await _vincular(google.cadastrar(mime="application/pdf", tamanho=str(arquivos_drive_teto() + 1)))
        ).status_code == 422
        assert (await _vincular(google.cadastrar(mime="application/pdf", trashed=True))).status_code == 404
        assert (await _vincular("naoexiste" + "0" * 12)).status_code == 404
        assert (await _vincular("curto")).status_code == 422
        assert (await _vincular("tem espaço e / barra")).status_code == 422
        assert await _total_fichas(db) == 0

    @pytest.mark.asyncio
    async def test_arquivo_que_sumiu_do_google_fica_marcado(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)
        ficha = (await _enviar(client, token, pasta["id"])).json()

        for identificador, item in list(google.itens.items()):
            if item["mimeType"] == "x":
                del google.itens[identificador]

        resposta = await client.get(f"/drive/arquivos/{ficha['id']}/conteudo", headers=_auth(token))
        assert resposta.status_code == 404
        lista = await client.get(f"/drive/pastas/{pasta['id']}/arquivos", headers=_auth(token))
        assert lista.json()[0]["ausente_no_google"] is True

    @pytest.mark.asyncio
    async def test_renova_o_token_uma_vez_quando_o_google_responde_401(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)

        renovacoes: list[str] = []

        async def _renovar(refresh):
            renovacoes.append(refresh)
            return {"access_token": "acesso-novo", "expires_in": 3600, "scope": oauth_google_drive.SCOPE}

        monkeypatch.setattr(oauth_google_drive, "refresh_access_token", _renovar)
        google.negar_primeira_com_401 = True
        resposta = await _enviar(client, token, pasta["id"])
        assert resposta.status_code == 201, resposta.text
        assert renovacoes == ["refresh-1"]
        tokens_usados = {chamada[2] for chamada in google.chamadas}
        assert tokens_usados == {"acesso-1", "acesso-novo"}

    @pytest.mark.asyncio
    async def test_refresh_revogado_pede_reconexao(self, cliente_auth, google, monkeypatch):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id, expires_in=10)
        pasta = await _pasta(client, token)

        async def _recusa(refresh):
            raise OAuthTokenExchangeError("invalid_grant")

        monkeypatch.setattr(oauth_google_drive, "refresh_access_token", _recusa)
        resposta = await _enviar(client, token, pasta["id"])
        assert resposta.status_code == 409
        assert google.chamadas == []

    @pytest.mark.asyncio
    async def test_apagar_a_pasta_nao_mexe_no_google(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)
        assert (await _enviar(client, token, pasta["id"])).status_code == 201
        chamadas_antes = len(google.chamadas)

        resposta = await client.delete(f"/drive/pastas/{pasta['id']}", headers=_auth(token))
        assert resposta.status_code == 204
        assert len(google.chamadas) == chamadas_antes
        assert await _total_fichas(db) == 0
        assert all(not item["trashed"] for item in google.itens.values())

    @pytest.mark.asyncio
    async def test_respostas_nunca_trazem_token_nem_id_do_google(self, cliente_auth, google):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        await _conectar(db, user_id)
        pasta = await _pasta(client, token)
        ficha = (await _enviar(client, token, pasta["id"])).json()

        textos = [
            (await client.get("/drive/google/status", headers=_auth(token))).text,
            (await client.get("/drive/pastas", headers=_auth(token))).text,
            (await client.get(f"/drive/pastas/{pasta['id']}/arquivos", headers=_auth(token))).text,
            json.dumps(ficha),
        ]
        for texto in textos:
            assert "acesso-1" not in texto
            assert "refresh-1" not in texto
            assert "google_folder_id" not in texto
            assert "google_file_id" not in texto
            assert "token" not in texto.lower()


def arquivos_drive_teto() -> int:
    return arquivos_drive.TAMANHO_MAX

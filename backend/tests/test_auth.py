"""Integração dos endpoints `/auth/*` contra o Postgres (transação por
teste, rollback no fim — ver `conftest.cliente_auth`).

Cobre o que o smoke manual (`scripts/smoke_auth.py`) fazia: cadastro, login,
cookie de refresh, rotação, logout, `/me` e recuperação de senha. Sem
e-SAJ, sem Playwright.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import generate_refresh_token
from app.main import app
from app.models.password_reset_token import PasswordResetToken

SENHA = "SenhaForte123!"
COOKIE_REFRESH = "refresh_token"


def _email() -> str:
    return f"pytest-auth-{uuid4().hex[:12]}@example.com"


def _corpo_cadastro(email: str, *, name: str = "Advogado Teste", password: str = SENHA) -> dict:
    return {"name": name, "email": email, "password": password}


async def _cadastrar(client, email: str | None = None):
    email = email or _email()
    resposta = await client.post("/auth/cadastro", json=_corpo_cadastro(email))
    return resposta, email


class TestCadastro:
    @pytest.mark.asyncio
    async def test_cria_sessao_sem_expor_password_hash(self, cliente_auth):
        client, _db = cliente_auth
        resposta, email = await _cadastrar(client)

        assert resposta.status_code == 201
        corpo = resposta.json()
        assert corpo["access_token"]
        assert corpo["token_type"] == "bearer"
        assert corpo["user"]["email"] == email
        assert "password_hash" not in corpo["user"]
        assert client.cookies.get(COOKIE_REFRESH)

    @pytest.mark.asyncio
    async def test_email_duplicado_retorna_409(self, cliente_auth):
        client, _db = cliente_auth
        primeira, email = await _cadastrar(client)
        assert primeira.status_code == 201

        segunda = await client.post("/auth/cadastro", json=_corpo_cadastro(email))
        assert segunda.status_code == 409

    @pytest.mark.asyncio
    async def test_payload_invalido_retorna_422(self, cliente_auth):
        client, _db = cliente_auth
        resposta = await client.post(
            "/auth/cadastro",
            json={"name": "A", "email": "nao-e-email", "password": "curta"},
        )
        assert resposta.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_ok_emite_sessao(self, cliente_auth):
        client, _db = cliente_auth
        _, email = await _cadastrar(client)
        client.cookies.clear()

        resposta = await client.post("/auth/login", json={"email": email, "password": SENHA})
        assert resposta.status_code == 200
        assert resposta.json()["access_token"]
        assert client.cookies.get(COOKIE_REFRESH)

    @pytest.mark.asyncio
    async def test_senha_errada_e_email_inexistente_sao_401_generico(self, cliente_auth):
        client, _db = cliente_auth
        _, email = await _cadastrar(client)

        senha_errada = await client.post(
            "/auth/login", json={"email": email, "password": "senha-errada"}
        )
        inexistente = await client.post(
            "/auth/login",
            json={"email": f"sumido-{uuid4().hex[:8]}@example.com", "password": SENHA},
        )

        assert senha_errada.status_code == 401
        assert inexistente.status_code == 401
        assert senha_errada.json()["detail"] == inexistente.json()["detail"]


class TestMe:
    @pytest.mark.asyncio
    async def test_com_token_devolve_usuario(self, cliente_auth):
        client, _db = cliente_auth
        cadastro, email = await _cadastrar(client)
        token = cadastro.json()["access_token"]

        resposta = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resposta.status_code == 200
        assert resposta.json()["email"] == email

    @pytest.mark.asyncio
    async def test_sem_token_ou_token_invalido_retorna_401(self, cliente_auth):
        client, _db = cliente_auth
        sem = await client.get("/auth/me")
        invalido = await client.get("/auth/me", headers={"Authorization": "Bearer token-invalido"})
        assert sem.status_code == 401
        assert invalido.status_code == 401


class TestRefreshELogout:
    @pytest.mark.asyncio
    async def test_refresh_rotaciona_cookie_e_emite_novo_access(self, cliente_auth):
        client, _db = cliente_auth
        cadastro, _email = await _cadastrar(client)
        access_antigo = cadastro.json()["access_token"]
        refresh_antigo = client.cookies.get(COOKIE_REFRESH)

        resposta = await client.post("/auth/refresh")
        assert resposta.status_code == 200
        assert resposta.json()["access_token"]
        assert resposta.json()["access_token"] != access_antigo
        assert client.cookies.get(COOKIE_REFRESH) not in (None, refresh_antigo)

        me = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {resposta.json()['access_token']}"},
        )
        assert me.status_code == 200

    @pytest.mark.asyncio
    async def test_reuso_do_refresh_antigo_retorna_401(self, cliente_auth):
        client, _db = cliente_auth
        await _cadastrar(client)
        refresh_antigo = client.cookies.get(COOKIE_REFRESH)
        assert refresh_antigo

        rotacao = await client.post("/auth/refresh")
        assert rotacao.status_code == 200

        # Cliente limpo: só o cookie já rotacionado — o jar do client
        # principal já tem o refresh novo e misturaria os dois.
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as outro:
            outro.cookies.set(COOKIE_REFRESH, refresh_antigo, path="/auth")
            reuso = await outro.post("/auth/refresh")
        assert reuso.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_revoga_e_refresh_posterior_falha(self, cliente_auth):
        client, _db = cliente_auth
        await _cadastrar(client)
        assert client.cookies.get(COOKIE_REFRESH)

        saida = await client.post("/auth/logout")
        assert saida.status_code == 200
        assert saida.json()["message"] == "Sessão encerrada"

        depois = await client.post("/auth/refresh")
        assert depois.status_code == 401


class TestRecuperarERedefinirSenha:
    @pytest.mark.asyncio
    async def test_recuperar_nao_revela_se_email_existe(self, cliente_auth):
        client, _db = cliente_auth
        _, email = await _cadastrar(client)

        existe = await client.post("/auth/recuperar-senha", json={"email": email})
        sumido = await client.post(
            "/auth/recuperar-senha",
            json={"email": f"inexistente-{uuid4().hex[:8]}@example.com"},
        )

        assert existe.status_code == 200
        assert sumido.status_code == 200
        assert existe.json() == sumido.json()

    @pytest.mark.asyncio
    async def test_redefinir_com_token_invalido_retorna_400(self, cliente_auth):
        client, _db = cliente_auth
        resposta = await client.post(
            "/auth/redefinir-senha",
            json={"token": "invalido", "new_password": SENHA},
        )
        assert resposta.status_code == 400

    @pytest.mark.asyncio
    async def test_redefinir_valido_troca_senha_e_token_nao_repete(self, cliente_auth):
        client, db = cliente_auth
        cadastro, email = await _cadastrar(client)
        user_id = UUID(cadastro.json()["user"]["id"])

        token, token_hash = generate_refresh_token()
        db.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        await db.flush()

        nova_senha = "OutraSenha123!"
        primeira = await client.post(
            "/auth/redefinir-senha",
            json={"token": token, "new_password": nova_senha},
        )
        assert primeira.status_code == 200

        segunda = await client.post(
            "/auth/redefinir-senha",
            json={"token": token, "new_password": nova_senha},
        )
        assert segunda.status_code == 400

        client.cookies.clear()
        antiga = await client.post("/auth/login", json={"email": email, "password": SENHA})
        nova = await client.post("/auth/login", json={"email": email, "password": nova_senha})
        assert antiga.status_code == 401
        assert nova.status_code == 200

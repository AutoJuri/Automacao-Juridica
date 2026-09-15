"""GET /credentials/email/provider-sugerido — sugestão de provedor por
MX (Etapa 9). Sem rede/DB real: `get_current_user` é sobrescrito e
`detectar_provedor_por_dominio` é monkeypatchado."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

import app.api.credentials as credentials_module
from app.api.deps import get_current_user
from app.main import app


def _user(email: str):
    return SimpleNamespace(id=uuid4(), email=email)


@pytest.fixture()
def client_factory():
    yield
    app.dependency_overrides.clear()


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestProviderSugerido:
    @pytest.mark.asyncio
    async def test_devolve_provedor_detectado(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user("advogado@gmail.com")
        monkeypatch.setattr(
            credentials_module, "detectar_provedor_por_dominio", lambda _email: "gmail"
        )

        async with await _client() as client:
            resposta = await client.get(
                "/credentials/email/provider-sugerido", headers={"Authorization": "Bearer x"}
            )

        assert resposta.status_code == 200
        assert resposta.json() == {"provider": "gmail"}

    @pytest.mark.asyncio
    async def test_sem_sugestao_devolve_provider_none(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user("advogado@dominio-raro.com")
        monkeypatch.setattr(
            credentials_module, "detectar_provedor_por_dominio", lambda _email: None
        )

        async with await _client() as client:
            resposta = await client.get(
                "/credentials/email/provider-sugerido", headers={"Authorization": "Bearer x"}
            )

        assert resposta.status_code == 200
        assert resposta.json() == {"provider": None}

    @pytest.mark.asyncio
    async def test_sem_autenticacao_e_rejeitado(self, client_factory):
        async with await _client() as client:
            resposta = await client.get("/credentials/email/provider-sugerido")

        assert resposta.status_code in (401, 403)

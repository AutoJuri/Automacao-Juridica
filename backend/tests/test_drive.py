"""Integração das pastas do Drive. A transação do teste faz rollback."""

from uuid import UUID, uuid4

import pytest

from app.models.processo import Processo

SENHA = "SenhaForte123!"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _cadastrar(client, *, name: str = "Marina") -> tuple[str, str]:
    resposta = await client.post(
        "/auth/cadastro",
        json={
            "name": name,
            "email": f"pytest-drive-{uuid4().hex[:12]}@example.com",
            "password": SENHA,
            "cargo": "advogado",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["access_token"], resposta.json()["user"]["id"]


async def _processo(db, user_id: str, numero: str) -> Processo:
    processo = Processo(
        user_id=UUID(user_id),
        tribunal="tjsp",
        cd_processo=uuid4().hex,
        nu_processo=numero,
        de_classe="Procedimento Comum",
        parte_ativa={"nome": "Autor Teste"},
        parte_passiva={"nome": "Reu Teste"},
    )
    db.add(processo)
    await db.commit()
    await db.refresh(processo)
    return processo


class TestPastasDoDrive:
    @pytest.mark.asyncio
    async def test_exige_login(self, cliente_auth):
        client, _db = cliente_auth
        assert (await client.get("/drive/pastas")).status_code == 401
        assert (await client.post("/drive/pastas", json={"nome": "x"})).status_code == 401

    @pytest.mark.asyncio
    async def test_criar_listar_renomear_excluir(self, cliente_auth):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)

        vazia = await client.get("/drive/pastas", headers=_auth(token))
        assert vazia.status_code == 200
        assert vazia.json() == []

        criada = await client.post(
            "/drive/pastas", json={"nome": "  Contratos  "}, headers=_auth(token)
        )
        assert criada.status_code == 201, criada.text
        corpo = criada.json()
        assert corpo["nome"] == "Contratos"
        assert corpo["processo"] is None
        assert corpo["total_arquivos"] == 0
        assert set(corpo) == {"id", "nome", "processo", "total_arquivos", "updated_at"}

        lista = await client.get("/drive/pastas", headers=_auth(token))
        assert [item["id"] for item in lista.json()] == [corpo["id"]]

        renomeada = await client.patch(
            f"/drive/pastas/{corpo['id']}", json={"nome": "Contratos 2026"}, headers=_auth(token)
        )
        assert renomeada.status_code == 200
        assert renomeada.json()["nome"] == "Contratos 2026"

        excluida = await client.delete(f"/drive/pastas/{corpo['id']}", headers=_auth(token))
        assert excluida.status_code == 204
        assert (await client.get(f"/drive/pastas/{corpo['id']}", headers=_auth(token))).status_code == 404

    @pytest.mark.asyncio
    async def test_nome_invalido_e_campo_extra(self, cliente_auth):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)

        for corpo in (
            {"nome": "   "},
            {"nome": ""},
            {"nome": "a" * 121},
            {"nome": "ok", "user_id": str(uuid4())},
            {"nome": "ok", "organization_id": str(uuid4())},
        ):
            resposta = await client.post("/drive/pastas", json=corpo, headers=_auth(token))
            assert resposta.status_code == 422, (corpo, resposta.text)

        criada = await client.post("/drive/pastas", json={"nome": "ok"}, headers=_auth(token))
        pasta_id = criada.json()["id"]
        for corpo in ({"nome": None}, {"nome": " "}, {"user_id": str(uuid4())}):
            resposta = await client.patch(
                f"/drive/pastas/{pasta_id}", json=corpo, headers=_auth(token)
            )
            assert resposta.status_code == 422, (corpo, resposta.text)

    @pytest.mark.asyncio
    async def test_pasta_de_outra_pessoa_e_404(self, cliente_auth):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)
        outro, _ = await _cadastrar(client, name="Ana")

        pasta = (
            await client.post("/drive/pastas", json={"nome": "Minha"}, headers=_auth(token))
        ).json()

        assert (await client.get("/drive/pastas", headers=_auth(outro))).json() == []
        assert (await client.get(f"/drive/pastas/{pasta['id']}", headers=_auth(outro))).status_code == 404
        assert (
            await client.patch(
                f"/drive/pastas/{pasta['id']}", json={"nome": "Roubada"}, headers=_auth(outro)
            )
        ).status_code == 404
        assert (
            await client.delete(f"/drive/pastas/{pasta['id']}", headers=_auth(outro))
        ).status_code == 404

        intacta = await client.get(f"/drive/pastas/{pasta['id']}", headers=_auth(token))
        assert intacta.json()["nome"] == "Minha"

    @pytest.mark.asyncio
    async def test_vinculo_com_processo(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        outro, outro_id = await _cadastrar(client, name="Ana")

        meu = await _processo(db, user_id, "0000001-00.2026.8.26.0100")
        alheio = await _processo(db, outro_id, "0000002-00.2026.8.26.0100")

        negado = await client.post(
            "/drive/pastas",
            json={"nome": "Alheia", "processo_id": str(alheio.id)},
            headers=_auth(token),
        )
        assert negado.status_code == 404

        criada = await client.post(
            "/drive/pastas",
            json={"nome": "Do processo", "processo_id": str(meu.id)},
            headers=_auth(token),
        )
        assert criada.status_code == 201, criada.text
        assert criada.json()["processo"] == {
            "id": str(meu.id),
            "nu_processo": "0000001-00.2026.8.26.0100",
            "autor": "Autor Teste",
            "reu": "Reu Teste",
        }

        troca_alheia = await client.patch(
            f"/drive/pastas/{criada.json()['id']}",
            json={"processo_id": str(alheio.id)},
            headers=_auth(token),
        )
        assert troca_alheia.status_code == 404

        solto = await client.patch(
            f"/drive/pastas/{criada.json()['id']}",
            json={"processo_id": None},
            headers=_auth(token),
        )
        assert solto.status_code == 200
        assert solto.json()["processo"] is None
        assert solto.json()["nome"] == "Do processo"

        renomeada = await client.patch(
            f"/drive/pastas/{criada.json()['id']}",
            json={"nome": "Outro nome"},
            headers=_auth(token),
        )
        assert renomeada.json()["processo"] is None

        _ = outro

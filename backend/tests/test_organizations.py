"""Integração de organizações e convites contra o Postgres.

A transação do teste dá rollback no fim (`conftest.cliente_auth`).
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.security import hash_token
from app.models.notification import NOTIFICATION_TIPO_CONVITE_ORG
from app.models.organization import OrganizationInvite
from app.services import organizations as orgs

SENHA = "SenhaForte123!"
TOKEN_FIXO = "33333333-3333-4333-8333-333333333333"


def _email() -> str:
    return f"pytest-org-{uuid4().hex[:12]}@example.com"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _cadastrar(client, *, name: str = "Advogado Teste", email: str | None = None):
    email = email or _email()
    resposta = await client.post(
        "/auth/cadastro",
        json={"name": name, "email": email, "password": SENHA, "cargo": "advogado"},
    )
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    return corpo["access_token"], email


async def _criar_org(client, token: str, nome: str = "Silva & Associados") -> dict:
    resposta = await client.post(
        "/organizations",
        json={"name": nome},
        headers=_auth(token),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


class TestCriarEIsolar:
    @pytest.mark.asyncio
    async def test_criador_vira_owner_e_estranho_recebe_403(self, cliente_auth):
        client, _db = cliente_auth
        dono, _email = await _cadastrar(client, name="Marina Silva")
        outro, _outro_email = await _cadastrar(client, name="João Autônomo")

        org = await _criar_org(client, dono)
        assert org["role"] == "owner"
        assert org["slug"] == "silva-associados"
        assert "password_hash" not in org

        lista = await client.get("/organizations", headers=_auth(dono))
        assert lista.status_code == 200
        assert lista.json()[0]["id"] == org["id"]
        assert lista.json()[0]["role"] == "owner"

        alheia = await client.get(f"/organizations/{org['id']}", headers=_auth(outro))
        assert alheia.status_code == 403

        convite = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": "alguem@example.com", "role": "advogado"},
            headers=_auth(outro),
        )
        assert convite.status_code == 403

    @pytest.mark.asyncio
    async def test_slug_repete_com_sufixo(self, cliente_auth):
        client, _db = cliente_auth
        primeiro, _ = await _cadastrar(client)
        segundo, _ = await _cadastrar(client)
        uma = await _criar_org(client, primeiro, "Silva")
        outra = await _criar_org(client, segundo, "Silva")
        assert uma["slug"] == "silva"
        assert outra["slug"] == "silva-2"


class TestConvites:
    @pytest.mark.asyncio
    async def test_listagem_nao_expoe_token_e_aceite_cria_membro(self, cliente_auth, monkeypatch):
        monkeypatch.setattr(orgs, "novo_token_convite", lambda: (TOKEN_FIXO, hash_token(TOKEN_FIXO)))
        client, db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        convidado, email_convidado = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)

        criado = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_convidado, "role": "advogado"},
            headers=_auth(dono),
        )
        assert criado.status_code == 201, criado.text
        corpo = criado.json()
        assert "token" not in corpo
        assert "token_hash" not in corpo
        assert corpo["email"] == email_convidado
        assert corpo["role"] == "advogado"

        lista = await client.get(f"/organizations/{org['id']}/invites", headers=_auth(dono))
        assert lista.status_code == 200
        assert "token" not in lista.text
        assert TOKEN_FIXO not in lista.text

        recebidos = await client.get("/organizations/invites/received", headers=_auth(convidado))
        assert recebidos.status_code == 200
        assert recebidos.json()[0]["organization_name"] == "Silva & Associados"
        assert "token" not in recebidos.text

        notificacoes = await client.get("/notifications", headers=_auth(convidado))
        assert notificacoes.status_code == 200
        convite_notif = [n for n in notificacoes.json() if n["tipo"] == NOTIFICATION_TIPO_CONVITE_ORG]
        assert len(convite_notif) == 1
        assert TOKEN_FIXO not in convite_notif[0]["message"]

        aceite = await client.post(
            f"/organizations/invites/received/{corpo['id']}/accept",
            headers=_auth(convidado),
        )
        assert aceite.status_code == 200, aceite.text
        assert aceite.json()["role"] == "advogado"

        membros = await client.get(f"/organizations/{org['id']}/members", headers=_auth(dono))
        emails = {m["email"] for m in membros.json()}
        assert email_convidado in emails
        assert all("password_hash" not in m for m in membros.json())

        convite_db = await db.get(OrganizationInvite, corpo["id"])
        assert convite_db is not None
        assert convite_db.accepted_at is not None
        assert convite_db.token_hash == hash_token(TOKEN_FIXO)

        reuso = await client.post(
            f"/organizations/invites/{TOKEN_FIXO}/accept",
            headers=_auth(convidado),
        )
        assert reuso.status_code == 400

    @pytest.mark.asyncio
    async def test_advogado_nao_convida(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        ana, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        convite = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "advogado"},
            headers=_auth(dono),
        )
        assert convite.status_code == 201
        aceite = await client.post(
            f"/organizations/invites/received/{convite.json()['id']}/accept",
            headers=_auth(ana),
        )
        assert aceite.status_code == 200

        bloqueado = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": _email(), "role": "assistente"},
            headers=_auth(ana),
        )
        assert bloqueado.status_code == 403

    @pytest.mark.asyncio
    async def test_token_de_outra_conta_retorna_403(self, cliente_auth, monkeypatch):
        monkeypatch.setattr(orgs, "novo_token_convite", lambda: (TOKEN_FIXO, hash_token(TOKEN_FIXO)))
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client)
        _ana, email_ana = await _cadastrar(client, name="Ana")
        intruso, _ = await _cadastrar(client, name="Intruso")
        org = await _criar_org(client, dono)
        await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "admin"},
            headers=_auth(dono),
        )

        resposta = await client.post(
            f"/organizations/invites/{TOKEN_FIXO}/accept",
            headers=_auth(intruso),
        )
        assert resposta.status_code == 403

    @pytest.mark.asyncio
    async def test_convite_expirado_retorna_400(self, cliente_auth, monkeypatch):
        monkeypatch.setattr(orgs, "novo_token_convite", lambda: (TOKEN_FIXO, hash_token(TOKEN_FIXO)))
        client, db = cliente_auth
        dono, _ = await _cadastrar(client)
        ana, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        criado = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "assistente"},
            headers=_auth(dono),
        )
        assert criado.status_code == 201

        convite = await db.scalar(
            select(OrganizationInvite).where(OrganizationInvite.token_hash == hash_token(TOKEN_FIXO))
        )
        assert convite is not None
        convite.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await db.commit()

        resposta = await client.post(
            f"/organizations/invites/{TOKEN_FIXO}/accept",
            headers=_auth(ana),
        )
        assert resposta.status_code == 400

    @pytest.mark.asyncio
    async def test_reenvio_invalida_o_token_anterior(self, cliente_auth, monkeypatch):
        tokens = iter(
            [
                ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", hash_token("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
                ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", hash_token("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")),
            ]
        )
        monkeypatch.setattr(orgs, "novo_token_convite", lambda: next(tokens))
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client)
        ana, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        primeiro = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "advogado"},
            headers=_auth(dono),
        )
        segundo = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "admin"},
            headers=_auth(dono),
        )
        assert primeiro.status_code == 201
        assert segundo.status_code == 201
        assert primeiro.json()["id"] == segundo.json()["id"]
        assert segundo.json()["role"] == "admin"

        antigo = await client.post(
            "/organizations/invites/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/accept",
            headers=_auth(ana),
        )
        assert antigo.status_code == 400

        novo = await client.post(
            "/organizations/invites/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/accept",
            headers=_auth(ana),
        )
        assert novo.status_code == 200
        assert novo.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_recusa_impede_aceite(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client)
        ana, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        convite = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "advogado"},
            headers=_auth(dono),
        )
        recusa = await client.post(
            f"/organizations/invites/received/{convite.json()['id']}/decline",
            headers=_auth(ana),
        )
        assert recusa.status_code == 204
        aceite = await client.post(
            f"/organizations/invites/received/{convite.json()['id']}/accept",
            headers=_auth(ana),
        )
        assert aceite.status_code == 404


class TestPapeis:
    @pytest.mark.asyncio
    async def test_admin_nao_altera_owner_e_transferencia_e_atomica(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        carlos, email_carlos = await _cadastrar(client, name="Carlos")
        org = await _criar_org(client, dono)
        convite = await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_carlos, "role": "admin"},
            headers=_auth(dono),
        )
        await client.post(
            f"/organizations/invites/received/{convite.json()['id']}/accept",
            headers=_auth(carlos),
        )

        membros = await client.get(f"/organizations/{org['id']}/members", headers=_auth(dono))
        por_email = {m["email"]: m for m in membros.json()}
        id_owner = next(m["id"] for m in membros.json() if m["role"] == "owner")
        id_carlos = por_email[email_carlos]["id"]

        alterar = await client.patch(
            f"/organizations/{org['id']}/members/{id_owner}",
            json={"role": "advogado"},
            headers=_auth(carlos),
        )
        assert alterar.status_code == 403

        promover = await client.patch(
            f"/organizations/{org['id']}/members/{id_carlos}",
            json={"role": "owner"},
            headers=_auth(dono),
        )
        assert promover.status_code == 422

        transferir = await client.post(
            f"/organizations/{org['id']}/members/{id_carlos}/transfer-ownership",
            headers=_auth(dono),
        )
        assert transferir.status_code == 204

        depois = await client.get(f"/organizations/{org['id']}/members", headers=_auth(carlos))
        papeis = {m["email"]: m["role"] for m in depois.json()}
        assert papeis[email_carlos] == "owner"
        marina = next(m for m in depois.json() if m["role"] == "admin")
        assert marina["name"] == "Marina"

        exclusao_admin = await client.delete(f"/organizations/{org['id']}", headers=_auth(dono))
        assert exclusao_admin.status_code == 403
        exclusao_owner = await client.delete(f"/organizations/{org['id']}", headers=_auth(carlos))
        assert exclusao_owner.status_code == 204

        sumiu = await client.get("/organizations", headers=_auth(carlos))
        assert sumiu.json() == []

    @pytest.mark.asyncio
    async def test_notificacao_nao_vai_para_quem_convidou(self, cliente_auth):
        client, _db = cliente_auth
        dono_token, _email_dono = await _cadastrar(client, name="Marina")
        _ana, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono_token)
        await client.post(
            f"/organizations/{org['id']}/invites",
            json={"email": email_ana, "role": "advogado"},
            headers=_auth(dono_token),
        )
        do_dono = await client.get("/notifications", headers=_auth(dono_token))
        assert do_dono.status_code == 200
        assert all(n["tipo"] != NOTIFICATION_TIPO_CONVITE_ORG for n in do_dono.json())

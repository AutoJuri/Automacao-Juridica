"""Integração da capa de elaboração. A transação do teste faz rollback."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models.elaboracao import Elaboracao
from app.models.processo import Processo

SENHA = "SenhaForte123!"


def _email() -> str:
    return f"pytest-elab-{uuid4().hex[:12]}@example.com"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _cadastrar(client, *, name: str = "Marina") -> tuple[str, str]:
    email = _email()
    resposta = await client.post(
        "/auth/cadastro",
        json={"name": name, "email": email, "password": SENHA, "cargo": "advogado"},
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


class TestElaboracoes:
    @pytest.mark.asyncio
    async def test_manual_isolamento_e_reabrir(self, cliente_auth):
        client, db = cliente_auth
        token, _user_id = await _cadastrar(client)
        outro, _ = await _cadastrar(client, name="Ana")

        criada = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "manual": {"titulo": "Peça avulsa", "parte_ativa": "João"}},
            headers=_auth(token),
        )
        assert criada.status_code == 201, criada.text
        corpo = criada.json()
        assert corpo["tem_processo"] is False
        assert corpo["titulo"] == "Peça avulsa"
        assert corpo["autor"] == "João"
        assert corpo["processo_id"] is None
        assert "password_hash" not in corpo
        elaboracao_id = corpo["id"]

        alheia = await client.get(f"/elaboracoes/{elaboracao_id}", headers=_auth(outro))
        assert alheia.status_code == 404

        lista_outro = await client.get("/elaboracoes", headers=_auth(outro))
        assert lista_outro.status_code == 200
        assert lista_outro.json() == []

        processo = await _processo(db, (await client.get("/auth/me", headers=_auth(outro))).json()["id"], "0000002-00.2026.8.26.0100")
        do_outro = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "processo_id": str(processo.id)},
            headers=_auth(token),
        )
        assert do_outro.status_code == 404

        invalida = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "manual": {"titulo": "x"}, "user_id": str(uuid4())},
            headers=_auth(token),
        )
        assert invalida.status_code == 422

    @pytest.mark.asyncio
    async def test_processo_reabre_e_sai_de_a_iniciar(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        meu = await _processo(db, user_id, "0000001-00.2026.8.26.0100")
        outro = await _processo(db, user_id, "0000003-00.2026.8.26.0100")

        antes = await client.get("/elaboracoes/a-iniciar", headers=_auth(token))
        assert antes.status_code == 200, antes.text
        assert antes.json()["total"] == 2
        ids = {item["id"] for item in antes.json()["items"]}
        assert ids == {str(meu.id), str(outro.id)}
        assert antes.json()["items"][0]["autor"] == "Autor Teste"

        primeira = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "processo_id": str(meu.id)},
            headers=_auth(token),
        )
        assert primeira.status_code == 201, primeira.text
        assert primeira.json()["tem_processo"] is True
        assert primeira.json()["nu_processo"] == "0000001-00.2026.8.26.0100"
        assert primeira.json()["manual"] is None

        de_novo = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "processo_id": str(meu.id)},
            headers=_auth(token),
        )
        assert de_novo.status_code == 200, de_novo.text
        assert de_novo.json()["id"] == primeira.json()["id"]
        linhas = list(
            (
                await db.scalars(
                    select(Elaboracao).where(Elaboracao.processo_id == meu.id)
                )
            ).all()
        )
        assert len(linhas) == 1

        outra_peca = await client.post(
            "/elaboracoes",
            json={"peca": "apelacao", "processo_id": str(meu.id)},
            headers=_auth(token),
        )
        assert outra_peca.status_code == 201, outra_peca.text
        assert outra_peca.json()["id"] != primeira.json()["id"]

        depois = await client.get("/elaboracoes/a-iniciar", headers=_auth(token))
        assert depois.json()["total"] == 1
        assert depois.json()["items"][0]["id"] == str(outro.id)

        em_andamento = await client.get("/elaboracoes", headers=_auth(token))
        assert len(em_andamento.json()) == 2

        conflito = await client.patch(
            f"/elaboracoes/{outra_peca.json()['id']}",
            json={"peca": "contestacao"},
            headers=_auth(token),
        )
        assert conflito.status_code == 409

        manual_no_processo = await client.patch(
            f"/elaboracoes/{primeira.json()['id']}",
            json={"manual": {"titulo": "Não pode"}},
            headers=_auth(token),
        )
        assert manual_no_processo.status_code == 409

    @pytest.mark.asyncio
    async def test_a_iniciar_pagina_de_doze(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        for indice in range(13):
            await _processo(db, user_id, f"00000{indice:02d}-00.2026.8.26.0100")

        pagina = await client.get("/elaboracoes/a-iniciar", headers=_auth(token))
        assert pagina.status_code == 200, pagina.text
        assert pagina.json()["total"] == 13
        assert len(pagina.json()["items"]) == 12

        resto = await client.get(
            "/elaboracoes/a-iniciar",
            params={"offset": 12},
            headers=_auth(token),
        )
        assert resto.status_code == 200, resto.text
        assert len(resto.json()["items"]) == 1
        assert resto.json()["total"] == 13

    @pytest.mark.asyncio
    async def test_excluir_so_a_propria(self, cliente_auth):
        client, _db = cliente_auth
        token, _ = await _cadastrar(client)
        outro, _ = await _cadastrar(client, name="Ana")
        criada = await client.post(
            "/elaboracoes",
            json={"peca": "memoriais", "manual": {"titulo": "Rascunho"}},
            headers=_auth(token),
        )
        assert criada.status_code == 201, criada.text
        elaboracao_id = criada.json()["id"]

        bloqueio = await client.delete(
            f"/elaboracoes/{elaboracao_id}",
            headers=_auth(outro),
        )
        assert bloqueio.status_code == 404

        ok = await client.delete(f"/elaboracoes/{elaboracao_id}", headers=_auth(token))
        assert ok.status_code == 204
        sumiu = await client.get(f"/elaboracoes/{elaboracao_id}", headers=_auth(token))
        assert sumiu.status_code == 404

    @pytest.mark.asyncio
    async def test_busca_acha_a_parte_passiva(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        alvo = Processo(
            user_id=UUID(user_id),
            tribunal="tjsp",
            cd_processo=uuid4().hex,
            nu_processo="0001111-00.2026.8.26.0100",
            de_classe="Procedimento Comum",
            de_assunto="Cobrança",
            parte_ativa={"nome": "Autor Distinto"},
            parte_passiva={"nome": "KABUM S/A"},
        )
        outro = Processo(
            user_id=UUID(user_id),
            tribunal="tjsp",
            cd_processo=uuid4().hex,
            nu_processo="0002222-00.2026.8.26.0100",
            de_classe="Procedimento Comum",
            parte_ativa={"nome": "Autor Distinto"},
            parte_passiva={"nome": "Outro Reu"},
        )
        db.add_all([alvo, outro])
        await db.commit()
        await db.refresh(alvo)

        lista = await client.get("/processos", params={"q": "kabum"}, headers=_auth(token))
        assert lista.status_code == 200, lista.text
        assert [item["id"] for item in lista.json()] == [str(alvo.id)]

        iniciar = await client.get(
            "/elaboracoes/a-iniciar", params={"q": "kabum"}, headers=_auth(token)
        )
        assert iniciar.status_code == 200, iniciar.text
        assert [item["id"] for item in iniciar.json()["items"]] == [str(alvo.id)]

        criada = await client.post(
            "/elaboracoes",
            json={"peca": "contestacao", "processo_id": str(alvo.id)},
            headers=_auth(token),
        )
        assert criada.status_code == 201, criada.text
        andamento = await client.get("/elaboracoes", params={"q": "kabum"}, headers=_auth(token))
        assert andamento.status_code == 200, andamento.text
        assert [item["id"] for item in andamento.json()] == [criada.json()["id"]]

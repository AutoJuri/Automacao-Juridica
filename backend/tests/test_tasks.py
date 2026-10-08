"""Integração do quadro de tarefas contra o Postgres.

A transação do teste dá rollback no fim (`conftest.cliente_auth`).
"""

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.models.processo import Processo
from app.models.task import KanbanBoard, KanbanColumn, Task
from app.services.tasks import hoje_em_sao_paulo

SENHA = "SenhaForte123!"
CAMPOS_PROIBIDOS = {
    "password_hash",
    "email",
    "cpf",
    "cpf_encrypted",
    "senha_encrypted",
    "cookie_encrypted",
    "token",
    "token_hash",
}


def _email() -> str:
    return f"pytest-task-{uuid4().hex[:12]}@example.com"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _chaves(valor: object) -> set[str]:
    if isinstance(valor, dict):
        achadas = set(valor)
        for item in valor.values():
            achadas |= _chaves(item)
        return achadas
    if isinstance(valor, list):
        achadas: set[str] = set()
        for item in valor:
            achadas |= _chaves(item)
        return achadas
    return set()


async def _cadastrar(client, *, name: str) -> tuple[str, str]:
    email = _email()
    resposta = await client.post(
        "/auth/cadastro",
        json={"name": name, "email": email, "password": SENHA, "cargo": "advogado"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["access_token"], email


async def _criar_org(client, token: str, nome: str = "Silva & Associados") -> dict:
    resposta = await client.post("/organizations", json={"name": nome}, headers=_auth(token))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


async def _convidar(client, dono: str, org_id: str, email: str, role: str) -> None:
    convite = await client.post(
        f"/organizations/{org_id}/invites",
        json={"email": email, "role": role},
        headers=_auth(dono),
    )
    assert convite.status_code == 201, convite.text
    aceite = await client.post(
        f"/organizations/invites/received/{convite.json()['id']}/accept",
        headers=_auth(
            (await client.post("/auth/login", json={"email": email, "password": SENHA})).json()[
                "access_token"
            ]
        ),
    )
    assert aceite.status_code == 200, aceite.text


async def _token_de(client, email: str) -> str:
    resposta = await client.post("/auth/login", json={"email": email, "password": SENHA})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["access_token"]


async def _board(client, token: str, org_id: str | None = None):
    caminho = "/tasks/board" if org_id is None else f"/organizations/{org_id}/tasks/board"
    resposta = await client.get(caminho, headers=_auth(token))
    return resposta


async def _membro_id(client, token: str, org_id: str, email: str) -> str:
    resposta = await client.get(f"/organizations/{org_id}/members", headers=_auth(token))
    assert resposta.status_code == 200, resposta.text
    return next(item["id"] for item in resposta.json() if item["email"] == email)


def _coluna(quadro: dict, titulo: str) -> dict:
    return next(coluna for coluna in quadro["columns"] if coluna["title"] == titulo)


class TestPessoal:
    @pytest.mark.asyncio
    async def test_seed_cria_move_e_resposta_sem_campo_sensivel(self, cliente_auth):
        client, _db = cliente_auth
        token, _email = await _cadastrar(client, name="Marina Silva")
        quadro = await _board(client, token)
        assert quadro.status_code == 200, quadro.text
        corpo = quadro.json()
        assert [coluna["title"] for coluna in corpo["columns"]] == [
            "A fazer",
            "Em andamento",
            "Concluído",
        ]
        assert sum(1 for coluna in corpo["columns"] if coluna["is_done"]) == 1
        assert _coluna(corpo, "Concluído")["is_done"] is True
        assert corpo["tasks"] == []

        a_fazer = _coluna(corpo, "A fazer")["id"]
        ontem = (hoje_em_sao_paulo() - timedelta(days=1)).isoformat()
        criada = await client.post(
            "/tasks",
            json={"title": "Protocolar", "column_id": a_fazer, "due_date": ontem},
            headers=_auth(token),
        )
        assert criada.status_code == 201, criada.text
        tarefa = criada.json()
        assert tarefa["is_overdue"] is True
        assert tarefa["assignee"]["member_id"] is None
        assert tarefa["assignee"]["name"] == "Marina Silva"
        assert tarefa["created_by"] == {"name": "Marina Silva"}
        assert CAMPOS_PROIBIDOS.isdisjoint(_chaves(tarefa))

        outra = await client.post(
            "/tasks",
            json={"title": "Revisar", "column_id": a_fazer},
            headers=_auth(token),
        )
        assert outra.status_code == 201, outra.text
        movida = await client.post(
            f"/tasks/{tarefa['id']}/move",
            json={"column_id": a_fazer, "position": 1},
            headers=_auth(token),
        )
        assert movida.status_code == 200, movida.text
        assert movida.json()["position"] == 1

        concluido = _coluna(corpo, "Concluído")["id"]
        feita = await client.post(
            f"/tasks/{tarefa['id']}/move",
            json={"column_id": concluido, "position": 0},
            headers=_auth(token),
        )
        assert feita.status_code == 200, feita.text
        assert feita.json()["completed_at"] is not None
        assert feita.json()["is_overdue"] is False

        de_volta = await client.post(
            f"/tasks/{tarefa['id']}/move",
            json={"column_id": a_fazer, "position": 0},
            headers=_auth(token),
        )
        assert de_volta.status_code == 200, de_volta.text
        assert de_volta.json()["completed_at"] is None
        assert de_volta.json()["is_overdue"] is True


class TestIsolamento:
    @pytest.mark.asyncio
    async def test_tarefa_de_outro_contexto_responde_404_e_estranho_403(self, cliente_auth):
        client, _db = cliente_auth
        marina, _ = await _cadastrar(client, name="Marina")
        joao, _ = await _cadastrar(client, name="João")
        org = await _criar_org(client, marina)
        outra = await _criar_org(client, marina, nome="Outro Escritório")

        quadro = (await _board(client, marina, org["id"])).json()
        coluna = _coluna(quadro, "A fazer")["id"]
        membros = await client.get(f"/organizations/{org['id']}/members", headers=_auth(marina))
        membro_id = membros.json()[0]["id"]
        criada = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Da organização",
                "column_id": coluna,
                "assigned_to_member_id": membro_id,
            },
            headers=_auth(marina),
        )
        assert criada.status_code == 201, criada.text
        tarefa_id = criada.json()["id"]

        pessoal = await client.patch(
            f"/tasks/{tarefa_id}",
            json={"title": "Invadiu"},
            headers=_auth(marina),
        )
        assert pessoal.status_code == 404

        do_joao = await client.patch(
            f"/tasks/{tarefa_id}",
            json={"title": "Invadiu"},
            headers=_auth(joao),
        )
        assert do_joao.status_code == 404

        outra_org = await client.patch(
            f"/organizations/{outra['id']}/tasks/{tarefa_id}",
            json={"title": "Invadiu"},
            headers=_auth(marina),
        )
        assert outra_org.status_code == 404

        alheia = await _board(client, joao, org["id"])
        assert alheia.status_code == 403


class TestPapeis:
    @pytest.mark.asyncio
    async def test_advogado_ve_so_a_sua_e_assistente_nao_mexe_na_alheia(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        ana_token, email_ana = await _cadastrar(client, name="Ana")
        bia_token, email_bia = await _cadastrar(client, name="Bia")
        caio_token, email_caio = await _cadastrar(client, name="Caio")
        org = await _criar_org(client, dono)
        await _convidar(client, dono, org["id"], email_ana, "advogado")
        await _convidar(client, dono, org["id"], email_bia, "assistente")
        await _convidar(client, dono, org["id"], email_caio, "admin")
        ana_token = await _token_de(client, email_ana)
        bia_token = await _token_de(client, email_bia)
        caio_token = await _token_de(client, email_caio)

        quadro = (await _board(client, dono, org["id"])).json()
        coluna = _coluna(quadro, "A fazer")["id"]
        ana_id = await _membro_id(client, dono, org["id"], email_ana)
        criada = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={"title": "Peça da Ana", "column_id": coluna, "assigned_to_member_id": ana_id},
            headers=_auth(dono),
        )
        assert criada.status_code == 201, criada.text
        tarefa_id = criada.json()["id"]

        vista_ana = (await _board(client, ana_token, org["id"])).json()
        assert [item["id"] for item in vista_ana["tasks"]] == [tarefa_id]
        vista_bia = (await _board(client, bia_token, org["id"])).json()
        assert vista_bia["tasks"] == []

        bloqueio = await client.post(
            f"/organizations/{org['id']}/tasks/{tarefa_id}/move",
            json={"column_id": coluna, "position": 0},
            headers=_auth(bia_token),
        )
        assert bloqueio.status_code == 404

        movida = await client.post(
            f"/organizations/{org['id']}/tasks/{tarefa_id}/move",
            json={"column_id": _coluna(quadro, "Em andamento")["id"], "position": 0},
            headers=_auth(ana_token),
        )
        assert movida.status_code == 200, movida.text

        exclusao_ana = await client.delete(
            f"/organizations/{org['id']}/tasks/{tarefa_id}",
            headers=_auth(ana_token),
        )
        assert exclusao_ana.status_code == 403

        admin = await client.post(
            f"/organizations/{org['id']}/tasks/{tarefa_id}/move",
            json={"column_id": coluna, "position": 0},
            headers=_auth(caio_token),
        )
        assert admin.status_code == 200, admin.text

        dono_exclui = await client.delete(
            f"/organizations/{org['id']}/tasks/{tarefa_id}",
            headers=_auth(dono),
        )
        assert dono_exclui.status_code == 204


class TestColunas:
    @pytest.mark.asyncio
    async def test_limite_remocao_e_uma_coluna_de_conclusao(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        ana_token, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        await _convidar(client, dono, org["id"], email_ana, "advogado")
        ana_token = await _token_de(client, email_ana)

        quadro = (await _board(client, dono, org["id"])).json()
        extra = await client.post(
            f"/organizations/{org['id']}/kanban/columns",
            json={"title": "Revisão"},
            headers=_auth(dono),
        )
        assert extra.status_code == 201, extra.text
        quinta = await client.post(
            f"/organizations/{org['id']}/kanban/columns",
            json={"title": "Extra"},
            headers=_auth(dono),
        )
        assert quinta.status_code == 409

        negada = await client.post(
            f"/organizations/{org['id']}/kanban/columns",
            json={"title": "Não posso"},
            headers=_auth(ana_token),
        )
        assert negada.status_code == 403

        a_fazer = _coluna(quadro, "A fazer")["id"]
        membro = await _membro_id(client, dono, org["id"], email_ana)
        tarefa = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={"title": "Ocupa", "column_id": a_fazer, "assigned_to_member_id": membro},
            headers=_auth(dono),
        )
        assert tarefa.status_code == 201, tarefa.text
        cheia = await client.delete(
            f"/organizations/{org['id']}/kanban/columns/{a_fazer}",
            headers=_auth(dono),
        )
        assert cheia.status_code == 409

        vazia = await client.delete(
            f"/organizations/{org['id']}/kanban/columns/{_coluna(quadro, 'Em andamento')['id']}",
            headers=_auth(dono),
        )
        assert vazia.status_code == 204
        await client.delete(
            f"/organizations/{org['id']}/kanban/columns/{extra.json()['id']}",
            headers=_auth(dono),
        )
        await client.delete(
            f"/organizations/{org['id']}/kanban/columns/{_coluna(quadro, 'Concluído')['id']}",
            headers=_auth(dono),
        )
        ultima = await client.delete(
            f"/organizations/{org['id']}/kanban/columns/{a_fazer}",
            headers=_auth(dono),
        )
        assert ultima.status_code == 409

        marcada = await client.patch(
            f"/organizations/{org['id']}/kanban/columns/{a_fazer}",
            json={"is_done": True},
            headers=_auth(dono),
        )
        assert marcada.status_code == 200, marcada.text
        atual = (await _board(client, dono, org["id"])).json()
        assert sum(1 for coluna in atual["columns"] if coluna["is_done"]) == 1
        assert _coluna(atual, "A fazer")["is_done"] is True


class TestVinculoENotificacao:
    @pytest.mark.asyncio
    async def test_processo_proprio_e_aviso_sem_dados_do_processo(self, cliente_auth):
        client, db = cliente_auth
        dono, email_dono = await _cadastrar(client, name="Marina")
        ana_token, email_ana = await _cadastrar(client, name="Ana")
        org = await _criar_org(client, dono)
        await _convidar(client, dono, org["id"], email_ana, "advogado")
        ana_token = await _token_de(client, email_ana)

        eu = await client.get("/auth/me", headers=_auth(dono))
        ana = await client.get("/auth/me", headers=_auth(ana_token))
        meu = Processo(
            user_id=UUID(eu.json()["id"]),
            tribunal="tjsp",
            cd_processo=uuid4().hex,
            nu_processo="0000001-00.2026.8.26.0100",
        )
        dela = Processo(
            user_id=UUID(ana.json()["id"]),
            tribunal="tjsp",
            cd_processo=uuid4().hex,
            nu_processo="0000002-00.2026.8.26.0100",
        )
        db.add(meu)
        db.add(dela)
        await db.commit()

        quadro = (await _board(client, dono, org["id"])).json()
        coluna = _coluna(quadro, "A fazer")["id"]
        ana_id = await _membro_id(client, dono, org["id"], email_ana)
        dono_id = await _membro_id(client, dono, org["id"], email_dono)
        alheio = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Com processo da Ana",
                "column_id": coluna,
                "assigned_to_member_id": ana_id,
                "processo_id": str(dela.id),
            },
            headers=_auth(dono),
        )
        assert alheio.status_code == 404

        criada = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Protocolar contestação",
                "column_id": coluna,
                "assigned_to_member_id": ana_id,
                "processo_id": str(meu.id),
            },
            headers=_auth(dono),
        )
        assert criada.status_code == 201, criada.text
        processo = criada.json()["processo"]
        assert set(processo) == {"id", "nu_processo"}
        assert processo["nu_processo"] == "0000001-00.2026.8.26.0100"

        avisos = await client.get("/notifications", headers=_auth(ana_token))
        atribuida = [item for item in avisos.json() if item["tipo"] == "task_atribuida"]
        assert len(atribuida) == 1
        assert atribuida[0]["message"] == "Protocolar contestação"
        assert "0000001" not in atribuida[0]["message"]
        assert atribuida[0]["task_id"] == criada.json()["id"]
        assert atribuida[0]["organization_id"] == org["id"]
        assert atribuida[0]["processo_id"] is None

        proprias = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Minha",
                "column_id": coluna,
                "assigned_to_member_id": dono_id,
            },
            headers=_auth(dono),
        )
        assert proprias.status_code == 201, proprias.text
        dono_avisos = await client.get("/notifications", headers=_auth(dono))
        assert [item for item in dono_avisos.json() if item["tipo"] == "task_atribuida"] == []

        fora = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Fora",
                "column_id": coluna,
                "assigned_to_member_id": str(uuid4()),
            },
            headers=_auth(dono),
        )
        assert fora.status_code == 400

        concluida = await client.post(
            f"/organizations/{org['id']}/tasks/{criada.json()['id']}/move",
            json={"column_id": _coluna(quadro, "Concluído")["id"], "position": 0},
            headers=_auth(ana_token),
        )
        assert concluida.status_code == 200, concluida.text
        dono_avisos = await client.get("/notifications", headers=_auth(dono))
        conclusoes = [item for item in dono_avisos.json() if item["tipo"] == "task_concluida"]
        assert len(conclusoes) == 1
        assert conclusoes[0]["message"] == "Protocolar contestação"
        assert "0000001" not in conclusoes[0]["message"]


class TestCascata:
    @pytest.mark.asyncio
    async def test_excluir_organizacao_apaga_tarefas_e_colunas(self, cliente_auth):
        client, db = cliente_auth
        dono, email_dono = await _cadastrar(client, name="Marina")
        org = await _criar_org(client, dono)
        quadro = (await _board(client, dono, org["id"])).json()
        membro = await _membro_id(client, dono, org["id"], email_dono)
        criada = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={
                "title": "Some com a org",
                "column_id": _coluna(quadro, "A fazer")["id"],
                "assigned_to_member_id": membro,
            },
            headers=_auth(dono),
        )
        assert criada.status_code == 201, criada.text
        nome = await client.patch(
            f"/organizations/{org['id']}/tasks/board",
            json={"title": "Quadro do escritório", "description": "Prazos da semana"},
            headers=_auth(dono),
        )
        assert nome.status_code == 200, nome.text
        apagada = await client.delete(f"/organizations/{org['id']}", headers=_auth(dono))
        assert apagada.status_code == 204, apagada.text
        org_id = UUID(org["id"])
        tarefas = await db.scalar(
            select(func.count()).select_from(Task).where(Task.organization_id == org_id)
        )
        colunas = await db.scalar(
            select(func.count()).select_from(KanbanColumn).where(KanbanColumn.organization_id == org_id)
        )
        quadros = await db.scalar(
            select(func.count()).select_from(KanbanBoard).where(KanbanBoard.organization_id == org_id)
        )
        assert tarefas == 0
        assert colunas == 0
        assert quadros == 0


class TestApresentacao:
    @pytest.mark.asyncio
    async def test_nome_do_quadro_e_pessoal_e_so_owner_admin_na_org(self, cliente_auth):
        client, _db = cliente_auth
        dono, _ = await _cadastrar(client, name="Marina")
        ana_token, email_ana = await _cadastrar(client, name="Ana")
        outro, _ = await _cadastrar(client, name="Joao")

        pessoal = (await _board(client, dono)).json()
        assert pessoal["title"] == "Tarefas"
        assert pessoal["description"] == "Suas tarefas. O responsável é você."

        editado = await client.patch(
            "/tasks/board",
            json={"title": "Meu gabinete", "description": "Prazos desta semana"},
            headers=_auth(dono),
        )
        assert editado.status_code == 200, editado.text
        assert editado.json()["title"] == "Meu gabinete"
        assert editado.json()["description"] == "Prazos desta semana"
        de_novo = (await _board(client, dono)).json()
        assert de_novo["title"] == "Meu gabinete"

        do_outro = (await _board(client, outro)).json()
        assert do_outro["title"] == "Tarefas"

        vazio = await client.patch(
            "/tasks/board",
            json={"title": "   ", "description": ""},
            headers=_auth(dono),
        )
        assert vazio.status_code == 422

        org = await _criar_org(client, dono)
        await _convidar(client, dono, org["id"], email_ana, "advogado")
        ana_token = await _token_de(client, email_ana)
        org_board = (await _board(client, dono, org["id"])).json()
        assert "organização" in org_board["description"]

        bloqueado = await client.patch(
            f"/organizations/{org['id']}/tasks/board",
            json={"title": "Não pode", "description": ""},
            headers=_auth(ana_token),
        )
        assert bloqueado.status_code == 403

        do_dono = await client.patch(
            f"/organizations/{org['id']}/tasks/board",
            json={"title": "Prazos do escritório", "description": ""},
            headers=_auth(dono),
        )
        assert do_dono.status_code == 200, do_dono.text
        assert do_dono.json()["title"] == "Prazos do escritório"
        assert do_dono.json()["description"] == ""
        pessoal_depois = (await _board(client, dono)).json()
        assert pessoal_depois["title"] == "Meu gabinete"


class TestPaginaConclusao:
    @pytest.mark.asyncio
    async def test_primeira_leitura_traz_dez_e_o_resto_vem_na_pagina(self, cliente_auth):
        client, _db = cliente_auth
        token, _email = await _cadastrar(client, name="Marina")
        quadro = (await _board(client, token)).json()
        feita = _coluna(quadro, "Concluído")["id"]
        aberta = _coluna(quadro, "A fazer")["id"]
        for indice in range(11):
            criada = await client.post(
                "/tasks",
                json={"title": f"Feita {indice}", "column_id": feita},
                headers=_auth(token),
            )
            assert criada.status_code == 201, criada.text

        corpo = (await _board(client, token)).json()
        visiveis = [item for item in corpo["tasks"] if item["column_id"] == feita]
        assert len(visiveis) == 10
        assert _coluna(corpo, "Concluído")["task_count"] == 11
        assert _coluna(corpo, "A fazer")["task_count"] == 0

        pagina = await client.get(
            f"/tasks/columns/{feita}/tasks",
            params={"offset": 10},
            headers=_auth(token),
        )
        assert pagina.status_code == 200, pagina.text
        assert pagina.json()["total"] == 11
        assert [item["title"] for item in pagina.json()["tasks"]] == ["Feita 10"]

        fora = await client.get(
            f"/tasks/columns/{aberta}/tasks",
            headers=_auth(token),
        )
        assert fora.status_code == 404

    @pytest.mark.asyncio
    async def test_assistente_nao_recebe_concluida_alheia(self, cliente_auth):
        client, _db = cliente_auth
        dono, email_dono = await _cadastrar(client, name="Marina")
        bia_token, email_bia = await _cadastrar(client, name="Bia")
        org = await _criar_org(client, dono)
        await _convidar(client, dono, org["id"], email_bia, "assistente")
        bia_token = await _token_de(client, email_bia)
        quadro = (await _board(client, dono, org["id"])).json()
        feita = _coluna(quadro, "Concluído")["id"]
        dono_id = await _membro_id(client, dono, org["id"], email_dono)
        criada = await client.post(
            f"/organizations/{org['id']}/tasks",
            json={"title": "Só da Marina", "column_id": feita, "assigned_to_member_id": dono_id},
            headers=_auth(dono),
        )
        assert criada.status_code == 201, criada.text

        pagina = await client.get(
            f"/organizations/{org['id']}/kanban/columns/{feita}/tasks",
            headers=_auth(bia_token),
        )
        assert pagina.status_code == 200, pagina.text
        assert pagina.json() == {"tasks": [], "total": 0}

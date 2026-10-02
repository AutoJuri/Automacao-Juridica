"""Testes da IA da elaboração (ADR-016).

Duas camadas:
- Unitários do `StubLLMProvider` e do `elaboracao_prompt` — sem banco.
- Integração das rotas `/elaboracoes/*` contra o Postgres real (mesma
  `cliente_auth` de `test_auth.py`): ownership (404 de processo/elaboração
  de outro usuário), schema nunca expõe bytes cifrados, round-trip completo
  do stub (gerar → chat → grifo) e o 409 de editar sem versão anterior.
"""

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.elaboracao import ORIGEM_GERACAO, ElaboracaoVersao
from app.services.elaboracao import (
    pausar_sugestao_automatica,
    retomar_sugestao_automatica,
    sugestao_em_pausa,
)
from app.services.elaboracao_prompt import montar_contexto_elaboracao, montar_enderecamento
from app.services.llm.contexto import (
    ElaboracaoContexto,
    FichaProcessoContexto,
    SinaisSugestaoPeca,
)
from app.services.llm.stub_provider import AVISO_MODO_TESTE, StubLLMProvider

SENHA = "SenhaForte123!"


def _email() -> str:
    return f"pytest-elaboracao-{uuid4().hex[:12]}@example.com"


async def _cadastrar(client, email: str | None = None):
    email = email or _email()
    resposta = await client.post(
        "/auth/cadastro",
        json={"name": "Advogado Teste", "email": email, "password": SENHA},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    return corpo["access_token"], corpo["user"]["id"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _criar_processo(db, user_id: str) -> str:
    from app.models.processo import Processo

    processo = Processo(
        user_id=user_id,
        tribunal="esaj_tjsp",
        cd_processo=f"cd-{uuid4().hex[:12]}",
        nu_processo="1234567-89.2024.8.26.0100",
        de_classe="Procedimento Comum Cível",
        de_assunto="Obrigação de Fazer",
        parte_ativa={"nome": "Maria Autora"},
        parte_passiva={"nome": "João Réu"},
        foro="Foro Central",
        vara="1ª Vara Cível",
        valor_acao="R$ 10.000,00",
    )
    db.add(processo)
    await db.flush()
    await db.refresh(processo)
    return str(processo.id)


async def _criar_intimacao(
    db, user_id: str, processo_id: str, *, titulo: str, dias_atras: int = 0
) -> None:
    from app.models.intimacao import Intimacao

    db.add(
        Intimacao(
            user_id=user_id,
            processo_id=processo_id,
            id_esaj=f"esaj-{uuid4().hex[:12]}",
            titulo=titulo,
            descricao=titulo,
            data_movimentacao=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    await db.flush()


async def _criar_movimentacao(db, processo_id: str, *, titulo: str) -> None:
    from app.models.movimentacao import Movimentacao

    db.add(
        Movimentacao(
            processo_id=processo_id,
            data_movimentacao=datetime(2026, 1, 1, tzinfo=timezone.utc),
            descricao=titulo,
            titulo=titulo,
        )
    )
    await db.flush()


class TestPausaSugestaoAutomatica:
    def teardown_method(self) -> None:
        retomar_sugestao_automatica()

    def test_depois_do_limite_a_sugestao_fica_em_pausa(self):
        retomar_sugestao_automatica()
        assert sugestao_em_pausa(agora=100.0) is False
        pausar_sugestao_automatica(agora=100.0)
        assert sugestao_em_pausa(agora=100.0) is True
        assert sugestao_em_pausa(agora=100.0 + 600) is False


class TestStubProviderGerarMinuta:
    @pytest.mark.asyncio
    async def test_html_avisa_modo_teste_e_usa_dados_da_ficha(self):
        contexto = ElaboracaoContexto(
            ficha=FichaProcessoContexto(
                cnj="1234567-89.2024.8.26.0100",
                classe="Procedimento Comum Cível",
                assunto="Obrigação de Fazer",
                autor="Maria Autora",
                reu="João Réu",
                foro="Foro Central",
                vara="1ª Vara Cível",
                juiz=None,
                valor_causa="R$ 10.000,00",
                enderecamento="EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL DO FORO CENTRAL",
            ),
            peca="contestacao",
            fatos_extras="O réu nunca foi notificado.",
        )

        html = await StubLLMProvider().gerar_minuta(contexto)

        assert AVISO_MODO_TESTE in html
        assert "style=" not in html
        assert "Maria Autora" in html
        assert "João Réu" in html
        assert "O réu nunca foi notificado." in html
        assert "<script" not in html.lower()

    @pytest.mark.asyncio
    async def test_sem_fatos_extras_usa_placeholder(self):
        contexto = ElaboracaoContexto(
            ficha=FichaProcessoContexto(
                cnj=None,
                classe=None,
                assunto=None,
                autor=None,
                reu=None,
                foro=None,
                vara=None,
                juiz=None,
                valor_causa=None,
                enderecamento="EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO",
            ),
            peca="peticao-inicial",
            fatos_extras=None,
        )

        html = await StubLLMProvider().gerar_minuta(contexto)

        assert "Nenhum fato extra foi informado" in html

    @pytest.mark.asyncio
    async def test_escapa_html_malicioso_nos_fatos_extras(self):
        contexto = ElaboracaoContexto(
            ficha=FichaProcessoContexto(
                cnj=None,
                classe=None,
                assunto=None,
                autor=None,
                reu=None,
                foro=None,
                vara=None,
                juiz=None,
                valor_causa=None,
                enderecamento="EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO",
            ),
            peca="contestacao",
            fatos_extras="<script>alert(1)</script>",
        )

        html = await StubLLMProvider().gerar_minuta(contexto)

        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestStubProviderEditarMinuta:
    @pytest.mark.asyncio
    async def test_chat_acrescenta_nota_com_a_instrucao(self):
        html_atual = "<p>Minuta original</p>"

        html_novo = await StubLLMProvider().editar_minuta(
            html_atual=html_atual, instrucao="Deixe mais formal", trecho_selecionado=None
        )

        assert html_atual in html_novo
        assert "Deixe mais formal" in html_novo

    @pytest.mark.asyncio
    async def test_grifo_substitui_o_trecho_quando_encontrado(self):
        html_atual = "<p>Este trecho é fraco e deve ser revisado.</p>"

        html_novo = await StubLLMProvider().editar_minuta(
            html_atual=html_atual,
            instrucao="Tornar mais incisivo",
            trecho_selecionado="é fraco",
        )

        assert "é fraco" not in html_novo or "grifo" in html_novo
        assert "Tornar mais incisivo" in html_novo

    @pytest.mark.asyncio
    async def test_grifo_com_trecho_que_nao_casa_nao_derruba_a_chamada(self):
        html_atual = "<p>Texto qualquer</p>"

        html_novo = await StubLLMProvider().editar_minuta(
            html_atual=html_atual,
            instrucao="Corrigir gramática",
            trecho_selecionado="trecho que não existe no html",
        )

        assert html_atual in html_novo
        assert "Corrigir gramática" in html_novo

    @pytest.mark.asyncio
    async def test_escapa_instrucao_maliciosa(self):
        html_novo = await StubLLMProvider().editar_minuta(
            html_atual="<p>ok</p>",
            instrucao="<img src=x onerror=alert(1)>",
            trecho_selecionado=None,
        )

        assert "<img" not in html_novo
        assert "&lt;img" in html_novo


class TestStubProviderSugerirPeca:
    @pytest.mark.asyncio
    async def test_sugere_contestacao_a_partir_do_titulo_da_intimacao(self):
        sinais = SinaisSugestaoPeca(
            classe=None,
            assunto=None,
            ultima_intimacao_titulo="Citação para apresentar defesa",
            ultima_movimentacao_titulo=None,
        )

        sugestao = await StubLLMProvider().sugerir_peca(sinais)

        assert sugestao is not None
        assert sugestao.peca == "contestacao"
        assert "stub" in sugestao.explicacao.lower()

    @pytest.mark.asyncio
    async def test_sem_sinal_nenhum_devolve_none(self):
        sinais = SinaisSugestaoPeca(
            classe=None,
            assunto=None,
            ultima_intimacao_titulo=None,
            ultima_movimentacao_titulo=None,
        )

        assert await StubLLMProvider().sugerir_peca(sinais) is None

    @pytest.mark.asyncio
    async def test_sinal_sem_palavra_chave_conhecida_devolve_none(self):
        sinais = SinaisSugestaoPeca(
            classe="Procedimento Comum Cível",
            assunto="Indenização por dano moral",
            ultima_intimacao_titulo="Ato ordinatório",
            ultima_movimentacao_titulo=None,
        )

        assert await StubLLMProvider().sugerir_peca(sinais) is None


class TestStubProviderExtrairPerfilEstilo:
    @pytest.mark.asyncio
    async def test_devolve_json_com_aviso_de_modo_stub(self):
        perfil_json = await StubLLMProvider().extrair_perfil_estilo(
            texto_amostra="Primeira frase. Segunda frase mais longa aqui."
        )

        perfil = json.loads(perfil_json)
        assert perfil["modo"] == "stub"
        assert perfil["palavras_amostra"] > 0
        assert "stub" in perfil["aviso"].lower()


class TestMontarEnderecamento:
    def test_com_vara_e_foro(self):
        processo = SimpleNamespace(vara="1ª Vara Cível", foro="Foro Central")
        assert montar_enderecamento(processo) == (
            "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL DO FORO CENTRAL"
        )

    def test_sem_vara_nem_foro(self):
        processo = SimpleNamespace(vara=None, foro=None)
        assert montar_enderecamento(processo) == "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO"


class TestMontarContextoElaboracao:
    def test_usa_partes_json_e_fatos_extras(self):
        processo = SimpleNamespace(
            nu_processo="1234567-89.2024.8.26.0100",
            de_classe="Procedimento Comum Cível",
            de_assunto="Obrigação de Fazer",
            parte_ativa={"nome": "Maria Autora"},
            parte_passiva={"nome": "João Réu"},
            foro="Foro Central",
            vara="1ª Vara Cível",
            juiz=None,
            valor_acao="R$ 10.000,00",
        )

        contexto = montar_contexto_elaboracao(
            processo,
            peca="contestacao",
            fatos_extras="Fato relevante.",
            estilo_perfil='{"modo": "stub"}',
        )

        assert contexto.ficha.autor == "Maria Autora"
        assert contexto.ficha.reu == "João Réu"
        assert contexto.peca == "contestacao"
        assert contexto.fatos_extras == "Fato relevante."
        assert contexto.estilo_perfil == '{"modo": "stub"}'
        assert contexto.jurisprudencia_marcada == ()


class TestOwnershipEFluxoCompleto:
    @pytest.mark.asyncio
    async def test_criar_elaboracao_com_processo_de_outro_usuario_retorna_404(self, cliente_auth):
        client, db = cliente_auth
        token_a, user_a = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_a)

        token_b, _user_b = await _cadastrar(client)

        resposta = await client.post(
            "/elaboracoes",
            json={"processo_id": processo_id, "peca": "contestacao"},
            headers=_headers(token_b),
        )
        assert resposta.status_code == 404

    @pytest.mark.asyncio
    async def test_criar_elaboracao_e_reabrir_a_mesma_sessao(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)

        primeira = await client.post(
            "/elaboracoes",
            json={"processo_id": processo_id, "peca": "contestacao"},
            headers=_headers(token),
        )
        assert primeira.status_code == 201
        corpo = primeira.json()
        assert corpo["fatos_extras"] is None
        assert set(corpo.keys()) == {
            "id",
            "processo_id",
            "peca",
            "fatos_extras",
            "estilo_perfil",
            "created_at",
            "updated_at",
        }

        segunda = await client.post(
            "/elaboracoes",
            json={"processo_id": processo_id, "peca": "contestacao"},
            headers=_headers(token),
        )
        assert segunda.status_code == 201
        assert segunda.json()["id"] == corpo["id"]

    @pytest.mark.asyncio
    async def test_fatos_extras_ficam_cifrados_no_banco_e_o_schema_nunca_expoe_bytes(
        self, cliente_auth
    ):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]

        resposta = await client.patch(
            f"/elaboracoes/{elaboracao_id}",
            json={"fatos_extras": "O réu foi citado por edital irregular."},
            headers=_headers(token),
        )
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo["fatos_extras"] == "O réu foi citado por edital irregular."
        assert "fatos_extras_encrypted" not in corpo

        from app.models.elaboracao import Elaboracao

        persistido = await db.get(Elaboracao, elaboracao_id)
        assert persistido.fatos_extras_encrypted is not None
        assert b"edital" not in persistido.fatos_extras_encrypted

    @pytest.mark.asyncio
    async def test_outro_usuario_nao_atualiza_fatos_extras_de_elaboracao_alheia(self, cliente_auth):
        client, db = cliente_auth
        token_a, user_a = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_a)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token_a),
            )
        ).json()["id"]

        token_b, _user_b = await _cadastrar(client)
        resposta = await client.patch(
            f"/elaboracoes/{elaboracao_id}",
            json={"fatos_extras": "Tentativa de acesso indevido."},
            headers=_headers(token_b),
        )
        assert resposta.status_code == 404

    @pytest.mark.asyncio
    async def test_editar_sem_versao_anterior_retorna_409(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]

        resposta = await client.post(
            f"/elaboracoes/{elaboracao_id}/editar",
            json={"instrucao": "Deixe mais formal"},
            headers=_headers(token),
        )
        assert resposta.status_code == 409

    @pytest.mark.asyncio
    async def test_versao_ilegivel_lista_vazia_e_editar_retorna_409(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]
        db.add(
            ElaboracaoVersao(
                elaboracao_id=elaboracao_id,
                origem=ORIGEM_GERACAO,
                conteudo_encrypted=b"blob-muito-curto",
                llm_provider="stub",
            )
        )
        await db.flush()

        lista = await client.get(
            f"/elaboracoes/{elaboracao_id}/versoes", headers=_headers(token)
        )
        assert lista.status_code == 200
        corpo = lista.json()
        assert len(corpo) == 1
        assert corpo[0]["conteudo_html"] == ""
        assert "conteudo_encrypted" not in corpo[0]

        edicao = await client.post(
            f"/elaboracoes/{elaboracao_id}/editar",
            json={"instrucao": "Deixe mais formal"},
            headers=_headers(token),
        )
        assert edicao.status_code == 409
        assert edicao.json()["detail"] == "A minuta anterior não pode ser lida."

    @pytest.mark.asyncio
    async def test_peca_fora_do_catalogo_retorna_422(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)

        resposta = await client.post(
            "/elaboracoes",
            json={"processo_id": processo_id, "peca": "peca-inventada"},
            headers=_headers(token),
        )
        assert resposta.status_code == 422

    @pytest.mark.asyncio
    async def test_fluxo_completo_gerar_chat_grifo_e_lista_versoes(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]
        await client.patch(
            f"/elaboracoes/{elaboracao_id}",
            json={"fatos_extras": "O réu nunca foi notificado."},
            headers=_headers(token),
        )

        gerada = await client.post(
            f"/elaboracoes/{elaboracao_id}/gerar", headers=_headers(token)
        )
        assert gerada.status_code == 200
        versao_1 = gerada.json()
        assert versao_1["origem"] == "geracao"
        assert versao_1["llm_provider"] == "stub"
        assert "conteudo_encrypted" not in versao_1
        assert "O réu nunca foi notificado." in versao_1["conteudo_html"]

        editada_chat = await client.post(
            f"/elaboracoes/{elaboracao_id}/editar",
            json={"instrucao": "Deixe o texto mais formal"},
            headers=_headers(token),
        )
        assert editada_chat.status_code == 200
        versao_2 = editada_chat.json()
        assert versao_2["origem"] == "chat"
        assert versao_2["trecho_selecionado"] is None
        assert "Deixe o texto mais formal" in versao_2["conteudo_html"]

        editada_grifo = await client.post(
            f"/elaboracoes/{elaboracao_id}/editar",
            json={
                "instrucao": "Tornar mais incisivo",
                "trecho_selecionado": "Pedidos de teste",
            },
            headers=_headers(token),
        )
        assert editada_grifo.status_code == 200
        versao_3 = editada_grifo.json()
        assert versao_3["origem"] == "grifo"
        assert versao_3["trecho_selecionado"] == "Pedidos de teste"

        lista = await client.get(
            f"/elaboracoes/{elaboracao_id}/versoes", headers=_headers(token)
        )
        assert lista.status_code == 200
        origens = [v["origem"] for v in lista.json()]
        assert origens == ["grifo", "chat", "geracao"]  # mais recente primeiro

        # Confere no banco que nada foi persistido em texto claro.
        versoes_no_banco = (
            await db.scalars(select(ElaboracaoVersao).where(ElaboracaoVersao.elaboracao_id == elaboracao_id))
        ).all()
        for versao in versoes_no_banco:
            assert b"incisivo" not in versao.conteudo_encrypted
            if versao.instrucao_encrypted:
                assert b"incisivo" not in versao.instrucao_encrypted

    @pytest.mark.asyncio
    async def test_versoes_e_gerar_de_elaboracao_inexistente_retornam_404(self, cliente_auth):
        client, _db = cliente_auth
        token, _user_id = await _cadastrar(client)
        elaboracao_id = uuid4()

        gerar = await client.post(
            f"/elaboracoes/{elaboracao_id}/gerar", headers=_headers(token)
        )
        versoes = await client.get(
            f"/elaboracoes/{elaboracao_id}/versoes", headers=_headers(token)
        )

        assert gerar.status_code == 404
        assert versoes.status_code == 404


class TestSugestaoPeca:
    @pytest.mark.asyncio
    async def test_processo_de_outro_usuario_retorna_404(self, cliente_auth):
        client, db = cliente_auth
        token_a, user_a = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_a)

        token_b, _user_b = await _cadastrar(client)
        resposta = await client.get(
            "/elaboracoes/sugestao-peca",
            params={"processo_id": processo_id},
            headers=_headers(token_b),
        )
        assert resposta.status_code == 404

    @pytest.mark.asyncio
    async def test_sugere_a_partir_do_titulo_da_intimacao_mais_recente(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        await _criar_intimacao(
            db, user_id, processo_id, titulo="Citação para apresentar defesa em 15 dias"
        )

        resposta = await client.get(
            "/elaboracoes/sugestao-peca",
            params={"processo_id": processo_id},
            headers=_headers(token),
        )
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo["peca"] == "contestacao"
        assert corpo["explicacao"]

    @pytest.mark.asyncio
    async def test_sem_sinal_devolve_peca_none_sem_erro(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)

        resposta = await client.get(
            "/elaboracoes/sugestao-peca",
            params={"processo_id": processo_id},
            headers=_headers(token),
        )
        assert resposta.status_code == 200
        assert resposta.json() == {"peca": None, "explicacao": None}


class TestEstiloPorTexto:
    @pytest.mark.asyncio
    async def test_elaboracao_de_outro_usuario_retorna_404(self, cliente_auth):
        client, db = cliente_auth
        token_a, user_a = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_a)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token_a),
            )
        ).json()["id"]

        token_b, _user_b = await _cadastrar(client)
        resposta = await client.post(
            f"/elaboracoes/{elaboracao_id}/estilo",
            json={"texto": "Texto de um modelo de peça qualquer."},
            headers=_headers(token_b),
        )
        assert resposta.status_code == 404

    @pytest.mark.asyncio
    async def test_fica_cifrado_no_banco_e_retorna_decriptado(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]

        resposta = await client.post(
            f"/elaboracoes/{elaboracao_id}/estilo",
            json={"texto": "Texto exclusivo do modelo desta peça de teste."},
            headers=_headers(token),
        )
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert "estilo_perfil_encrypted" not in corpo
        perfil = json.loads(corpo["estilo_perfil"])
        assert perfil["modo"] == "stub"

        from app.models.elaboracao import Elaboracao

        persistido = await db.get(Elaboracao, elaboracao_id)
        assert persistido.estilo_perfil_encrypted is not None
        assert b"exclusivo" not in persistido.estilo_perfil_encrypted

    @pytest.mark.asyncio
    async def test_estilo_influencia_o_pacote_enviado_ao_gerar(self, cliente_auth):
        client, db = cliente_auth
        token, user_id = await _cadastrar(client)
        processo_id = await _criar_processo(db, user_id)
        elaboracao_id = (
            await client.post(
                "/elaboracoes",
                json={"processo_id": processo_id, "peca": "contestacao"},
                headers=_headers(token),
            )
        ).json()["id"]
        await client.post(
            f"/elaboracoes/{elaboracao_id}/estilo",
            json={"texto": "Modelo de peça com tom bastante formal."},
            headers=_headers(token),
        )

        gerada = await client.post(
            f"/elaboracoes/{elaboracao_id}/gerar", headers=_headers(token)
        )
        assert gerada.status_code == 200
        assert "Perfil de estilo aplicado" in gerada.json()["conteudo_html"]

    @pytest.mark.asyncio
    async def test_elaboracao_inexistente_retorna_404(self, cliente_auth):
        client, _db = cliente_auth
        token, _user_id = await _cadastrar(client)

        resposta = await client.post(
            f"/elaboracoes/{uuid4()}/estilo",
            json={"texto": "Qualquer texto."},
            headers=_headers(token),
        )
        assert resposta.status_code == 404

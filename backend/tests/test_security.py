"""Testes das primitivas de segurança (padrão AAA)."""

from datetime import timedelta
from uuid import uuid4

import bcrypt
import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    JWT_ALGORITHM,
    TokenInvalidoError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_password_or_dummy,
)

TOKEN_EXP_DISTANTE = 9999999999


class TestHashDeSenha:
    def test_senha_correta_valida(self):
        senha = "senha-super-secreta-123"

        hashed = hash_password(senha)

        assert verify_password(senha, hashed) is True

    def test_senha_errada_nao_valida(self):
        hashed = hash_password("senha-super-secreta-123")

        assert verify_password("outra-senha", hashed) is False

    def test_hashes_da_mesma_senha_sao_diferentes(self):
        senha = "senha-super-secreta-123"

        primeiro = hash_password(senha)
        segundo = hash_password(senha)

        assert primeiro != segundo  # salt aleatório por hash

    def test_hash_nao_contem_a_senha(self):
        senha = "senha-super-secreta-123"

        hashed = hash_password(senha)

        assert senha not in hashed

    def test_senha_acima_do_limite_do_bcrypt_e_rejeitada(self):
        senha = "a" * 73

        with pytest.raises(ValueError):
            hash_password(senha)

    def test_hash_malformado_nao_valida(self):
        assert verify_password("qualquer-senha", "nao-e-um-hash-bcrypt") is False


class TestVerifyPasswordOrDummy:
    def test_hash_none_ainda_executa_bcrypt_e_retorna_false(self, monkeypatch):
        """Sem usuário (hash None), o resultado é sempre False, mas o bcrypt
        real precisa ter sido chamado — é isso que equaliza o tempo de
        resposta do login entre e-mail existente e inexistente."""
        checkpw_foi_chamado = False
        checkpw_original = bcrypt.checkpw

        def checkpw_espiao(password: bytes, hashed: bytes) -> bool:
            nonlocal checkpw_foi_chamado
            checkpw_foi_chamado = True
            return checkpw_original(password, hashed)

        monkeypatch.setattr(bcrypt, "checkpw", checkpw_espiao)

        resultado = verify_password_or_dummy("qualquer-senha", None)

        assert resultado is False
        assert checkpw_foi_chamado is True

    def test_hash_real_com_senha_correta_valida(self):
        senha = "senha-super-secreta-123"
        hashed = hash_password(senha)

        assert verify_password_or_dummy(senha, hashed) is True

    def test_hash_real_com_senha_errada_nao_valida(self):
        hashed = hash_password("senha-super-secreta-123")

        assert verify_password_or_dummy("outra-senha", hashed) is False


class TestAccessToken:
    def test_roundtrip_devolve_o_mesmo_user_id(self):
        user_id = uuid4()

        token = create_access_token(user_id)

        assert decode_access_token(token) == user_id

    def test_token_expirado_e_rejeitado(self):
        token = create_access_token(uuid4(), expires_delta=timedelta(seconds=-1))

        with pytest.raises(TokenInvalidoError):
            decode_access_token(token)

    def test_token_adulterado_e_rejeitado(self):
        token = create_access_token(uuid4())
        adulterado = token[:-2] + ("cd" if token.endswith("ab") else "ab")

        with pytest.raises(TokenInvalidoError):
            decode_access_token(adulterado)

    def test_token_assinado_com_outro_segredo_e_rejeitado(self):
        token = jwt.encode(
            {"sub": str(uuid4()), "type": "access", "exp": TOKEN_EXP_DISTANTE},
            "segredo-do-atacante",
            algorithm=JWT_ALGORITHM,
        )

        with pytest.raises(TokenInvalidoError):
            decode_access_token(token)

    def test_token_com_alg_none_e_rejeitado(self):
        token = jwt.encode(
            {"sub": str(uuid4()), "type": "access", "exp": TOKEN_EXP_DISTANTE},
            key="",
            algorithm="none",
        )

        with pytest.raises(TokenInvalidoError):
            decode_access_token(token)

    def test_token_de_outro_tipo_e_rejeitado(self):
        token = jwt.encode(
            {"sub": str(uuid4()), "type": "refresh", "exp": TOKEN_EXP_DISTANTE},
            get_settings().jwt_secret,
            algorithm=JWT_ALGORITHM,
        )

        with pytest.raises(TokenInvalidoError):
            decode_access_token(token)

    def test_token_sem_exp_e_rejeitado(self):
        token = jwt.encode(
            {"sub": str(uuid4()), "type": "access"},
            get_settings().jwt_secret,
            algorithm=JWT_ALGORITHM,
        )

        with pytest.raises(TokenInvalidoError):
            decode_access_token(token)

    def test_payload_carrega_apenas_o_minimo(self):
        token = create_access_token(uuid4())

        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[JWT_ALGORITHM])

        assert set(payload) == {"sub", "type", "iat", "exp"}


class TestRefreshToken:
    def test_token_bruto_difere_do_hash_persistido(self):
        token, token_hash = generate_refresh_token()

        assert token != token_hash
        assert token not in token_hash

    def test_hash_e_deterministico(self):
        token, token_hash = generate_refresh_token()

        assert hash_token(token) == token_hash

    def test_hash_tem_tamanho_de_sha256_hex(self):
        _, token_hash = generate_refresh_token()

        assert len(token_hash) == 64

    def test_tokens_gerados_sao_distintos(self):
        tokens = {generate_refresh_token()[0] for _ in range(100)}

        assert len(tokens) == 100

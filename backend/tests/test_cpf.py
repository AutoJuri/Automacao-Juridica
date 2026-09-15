"""Testes de validação e mascaramento de CPF (padrão AAA)."""

import pytest

from app.core.cpf import is_valid_cpf, mask_cpf, normalize_cpf

CPF_VALIDO = "11144477735"


class TestNormalizeCpf:
    def test_remove_pontuacao(self):
        assert normalize_cpf("111.444.777-35") == CPF_VALIDO

    def test_ja_normalizado_permanece_igual(self):
        assert normalize_cpf(CPF_VALIDO) == CPF_VALIDO


class TestIsValidCpf:
    def test_cpf_valido_e_aceito(self):
        assert is_valid_cpf(CPF_VALIDO) is True

    def test_digito_verificador_errado_e_rejeitado(self):
        cpf_adulterado = CPF_VALIDO[:-1] + ("0" if CPF_VALIDO[-1] != "0" else "1")

        assert is_valid_cpf(cpf_adulterado) is False

    def test_todos_os_digitos_iguais_sao_rejeitados(self):
        assert is_valid_cpf("11111111111") is False
        assert is_valid_cpf("00000000000") is False

    def test_tamanho_errado_e_rejeitado(self):
        assert is_valid_cpf("123") is False
        assert is_valid_cpf(CPF_VALIDO + "9") is False

    def test_caracteres_nao_numericos_sao_rejeitados(self):
        assert is_valid_cpf("111.444.777-35") is False  # precisa vir normalizado


class TestMaskCpf:
    def test_formato_esperado(self):
        assert mask_cpf(CPF_VALIDO) == "***.444.777-**"

    def test_rejeita_cpf_fora_do_padrao(self):
        with pytest.raises(ValueError):
            mask_cpf("123")

"""Validação e mascaramento de CPF (documento do advogado no e-SAJ).

Este módulo nunca lida com dado criptografado — serve só para: (1) recusar
um CPF estruturalmente inválido antes de gastar uma chamada de AES-256 e (2)
gerar a versão mascarada que os endpoints devolvem ao frontend, sem nunca
precisar decriptar o valor real para exibição.
"""

import re

CPF_DIGITS = 11
_NAO_DIGITO = re.compile(r"\D")


def normalize_cpf(cpf: str) -> str:
    """Remove pontuação e espaços, deixando só os dígitos."""
    return _NAO_DIGITO.sub("", cpf)


def is_valid_cpf(cpf: str) -> bool:
    """Valida os dois dígitos verificadores do CPF.

    Espera `cpf` já normalizado (11 dígitos, sem pontuação) — use
    `normalize_cpf` antes se o valor ainda estiver formatado.
    """
    if len(cpf) != CPF_DIGITS or not cpf.isdigit():
        return False
    if cpf == cpf[0] * CPF_DIGITS:
        # 000.000.000-00, 111.111.111-11 etc. passam no cálculo dos dígitos
        # verificadores, mas a Receita Federal nunca emite CPF com todos os
        # dígitos iguais — a maioria das implementações trata como inválido.
        return False

    digitos = [int(d) for d in cpf]

    def _digito_verificador(fatia: list[int]) -> int:
        peso_inicial = len(fatia) + 1
        soma = sum(digito * (peso_inicial - indice) for indice, digito in enumerate(fatia))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    if _digito_verificador(digitos[:9]) != digitos[9]:
        return False
    return _digito_verificador(digitos[:10]) == digitos[10]


def mask_cpf(cpf: str) -> str:
    """Formata um CPF de 11 dígitos como `***.456.789-**`.

    Só chamar com um CPF já validado por `is_valid_cpf` — a máscara assume
    exatamente 11 dígitos numéricos e não revalida o checksum.
    """
    if len(cpf) != CPF_DIGITS or not cpf.isdigit():
        raise ValueError("mask_cpf espera exatamente 11 dígitos numéricos")
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"

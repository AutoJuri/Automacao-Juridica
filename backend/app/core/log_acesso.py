"""Tira o número CNJ da linha de acesso do Uvicorn.

A consulta pública vai na URL (`?numero=`). O logger da aplicação não grava
esse número; o access log do Uvicorn grava a URL inteira. Aqui o valor
some antes de a linha ser escrita.
"""

import logging
import re

_NUMERO = re.compile(r"(numero=)[^&\s\"]+")
_LOGGER = "uvicorn.access"


class _RedigeNumeroCnj(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(_redigir(item) for item in record.args)
        elif isinstance(record.args, dict):
            record.args = {chave: _redigir(valor) for chave, valor in record.args.items()}
        return True


def _redigir(valor: object) -> object:
    if not isinstance(valor, str):
        return valor
    return _NUMERO.sub(r"\1***", valor)


def instalar_redacao_de_numero() -> None:
    logger = logging.getLogger(_LOGGER)
    if any(isinstance(filtro, _RedigeNumeroCnj) for filtro in logger.filters):
        return
    logger.addFilter(_RedigeNumeroCnj())

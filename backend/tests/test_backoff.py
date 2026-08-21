"""Testes de app.core.backoff.calcular_proximo_retry (função pura)."""

from datetime import UTC, datetime

from app.core.backoff import BACKOFF_MINUTOS, calcular_proximo_retry


class TestCalcularProximoRetry:
    def test_primeira_falha_usa_primeiro_backoff(self):
        agora = datetime.now(UTC)
        resultado = calcular_proximo_retry(1)

        delta_min = round((resultado - agora).total_seconds() / 60)
        assert delta_min == BACKOFF_MINUTOS[0]

    def test_segunda_falha_usa_segundo_backoff(self):
        agora = datetime.now(UTC)
        resultado = calcular_proximo_retry(2)

        delta_min = round((resultado - agora).total_seconds() / 60)
        assert delta_min == BACKOFF_MINUTOS[1]

    def test_terceira_falha_usa_terceiro_backoff(self):
        agora = datetime.now(UTC)
        resultado = calcular_proximo_retry(3)

        delta_min = round((resultado - agora).total_seconds() / 60)
        assert delta_min == BACKOFF_MINUTOS[2]

    def test_falhas_acima_do_tamanho_da_tabela_usam_o_ultimo_backoff(self):
        agora = datetime.now(UTC)
        resultado = calcular_proximo_retry(10)

        delta_min = round((resultado - agora).total_seconds() / 60)
        assert delta_min == BACKOFF_MINUTOS[-1]

    def test_zero_ou_negativo_usa_o_primeiro_backoff(self):
        agora = datetime.now(UTC)
        resultado = calcular_proximo_retry(0)

        delta_min = round((resultado - agora).total_seconds() / 60)
        assert delta_min == BACKOFF_MINUTOS[0]

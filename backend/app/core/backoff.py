"""Backoff compartilhado para novas tentativas após falha.

Usado tanto pela validação de login (`credential_validation.py`, falha no
Playwright) quanto pelo rate limit dos pipes de coleta (`coleta_esaj.py`,
HTTP 429 do e-SAJ) — mesma escala de espera para os dois casos, já que o
recurso limitado do outro lado (e-SAJ) é o mesmo.
"""

from datetime import UTC, datetime, timedelta

# 1ª falha: 5min, 2ª: 15min, 3ª+: 60min. Quem efetivamente respeita esse
# campo e agenda o novo disparo é o scheduler (`app/core/scheduler.py`) —
# aqui é só o cálculo puro do próximo instante permitido.
BACKOFF_MINUTOS = (5, 15, 60)


def calcular_proximo_retry(tentativas_falha: int) -> datetime:
    indice = min(max(tentativas_falha - 1, 0), len(BACKOFF_MINUTOS) - 1)
    return datetime.now(UTC) + timedelta(minutes=BACKOFF_MINUTOS[indice])


__all__ = ["BACKOFF_MINUTOS", "calcular_proximo_retry"]

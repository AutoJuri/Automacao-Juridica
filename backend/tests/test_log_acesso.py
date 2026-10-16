import logging

from app.core.log_acesso import instalar_redacao_de_numero


def test_access_log_nao_grava_o_cnj(caplog):
    instalar_redacao_de_numero()
    logger = logging.getLogger("uvicorn.access")
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        logger.info(
            '%s - "%s %s"',
            "127.0.0.1",
            "GET",
            "/processos/publico?numero=1020590-88.2025.8.26.0071",
        )
    assert "1020590-88.2025.8.26.0071" not in caplog.text
    assert "numero=***" in caplog.text

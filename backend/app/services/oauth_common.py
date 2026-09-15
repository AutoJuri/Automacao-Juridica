"""Utilidades compartilhadas pelos dois provedores de OAuth2 de e-mail."""

# Timeout curto: a API externa (Google/Microsoft) não pode travar a resposta
# do nosso callback indefinidamente — mesma lógica do timeout de 10s aplicado
# ao DataJud em `security.mdc`.
OAUTH_HTTP_TIMEOUT_SECONDS = 10.0


class OAuthTokenExchangeError(Exception):
    """Falha ao trocar o `code` por tokens junto ao provedor (Google/Microsoft)."""

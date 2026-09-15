FROM python:3.12-slim

# UV — pin por digest (não a tag `latest`). Digest de `astral/uv:latest`
# em 2026-09-15; ghcr.io/astral-sh/uv é a mesma imagem.
COPY --from=ghcr.io/astral-sh/uv@sha256:62f8c047d0a0e9ece6b53fc63df902585a67a47a7f318ddec4a37db586edc8e3 /uv /usr/local/bin/uv

WORKDIR /app

# Dependências Python via UV (lockfile garante reprodutibilidade)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Chromium do Playwright (não o pacote `chromium` do Debian): o código chama
# `playwright.chromium.launch()` e procura o browser neste path. Instalar
# como root e deixar o diretório legível para o `appuser`.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright \
    && DEBIAN_FRONTEND=noninteractive uv run playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright

RUN useradd -m appuser && chown -R appuser /app /ms-playwright
USER appuser

# Railway injeta PORT. Localmente o default 8000 continua válido.
EXPOSE 8000

# --proxy-headers + --forwarded-allow-ips: o Railway termina TLS num proxy e
# encaminha o IP real via X-Forwarded-For. Sem isso, get_remote_address() do
# rate limiter vê o IP do proxy para todas as requisições — o limite por IP
# das rotas /auth/* deixa de funcionar (todo mundo cai no mesmo balde).
# "*" é aceitável aqui porque o único hop entre o cliente e este processo é o
# edge do Railway, não um proxy arbitrário controlado por terceiros.
CMD ["sh", "-c", "exec uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]

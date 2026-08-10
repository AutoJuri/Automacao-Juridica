FROM python:3.12-slim

# UV — gerenciador de pacotes
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependências de sistema do Playwright (Chromium) — usadas nas próximas etapas
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python via UV (lockfile garante reprodutibilidade)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# --proxy-headers + --forwarded-allow-ips: o Railway termina TLS num proxy e
# encaminha o IP real via X-Forwarded-For. Sem isso, get_remote_address() do
# rate limiter vê o IP do proxy para todas as requisições — o limite por IP
# das rotas /auth/* deixa de funcionar (todo mundo cai no mesmo balde).
# "*" é aceitável aqui porque o único hop entre o cliente e este processo é o
# edge do Railway, não um proxy arbitrário controlado por terceiros.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

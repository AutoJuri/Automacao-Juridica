"""Smoke test manual do fluxo de autenticação contra um servidor local.

Uso: python -m uv run python scripts/smoke_auth.py
Não faz parte da suíte automatizada — depende de servidor e banco reais.
"""

import json
import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from uuid import uuid4

BASE_URL = "http://localhost:8000"

cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

falhas: list[str] = []


def chamar(
    metodo: str,
    caminho: str,
    corpo: dict | None = None,
    token: str | None = None,
) -> tuple[int, dict]:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(f"{BASE_URL}{caminho}", data=dados, method=metodo)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with opener.open(req) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def verificar(descricao: str, condicao: bool) -> None:
    print(f"{'OK   ' if condicao else 'FALHA'} {descricao}")
    if not condicao:
        falhas.append(descricao)


def cookie_refresh() -> str | None:
    return next((c.value for c in cookie_jar if c.name == "refresh_token"), None)


def encerrar() -> None:
    print()
    if falhas:
        print(f"{len(falhas)} verificacao(oes) falharam:")
        for falha in falhas:
            print(f"  - {falha}")
        sys.exit(1)
    print("Todas as verificacoes passaram.")


def main() -> None:
    email = f"smoke-{uuid4().hex[:12]}@example.com"
    senha = "SenhaForte123!"

    status, body = chamar(
        "POST", "/auth/cadastro", {"name": "Smoke", "email": email, "password": senha}
    )
    verificar("cadastro retorna 201", status == 201)
    verificar("cadastro devolve access_token", bool(body.get("access_token")))
    verificar(
        "cadastro devolve o usuario sem password_hash", "password_hash" not in body.get("user", {})
    )
    verificar("cadastro seta cookie de refresh", cookie_refresh() is not None)
    access_token = body.get("access_token", "")

    status, _ = chamar(
        "POST", "/auth/cadastro", {"name": "Smoke", "email": email, "password": senha}
    )
    verificar("cadastro duplicado retorna 409", status == 409)

    status, body = chamar("GET", "/auth/me", token=access_token)
    verificar("me retorna 200 com token valido", status == 200)
    verificar("me devolve o email cadastrado", body.get("email") == email)

    status, _ = chamar("GET", "/auth/me")
    verificar("me sem token retorna 401", status == 401)

    status, _ = chamar("GET", "/auth/me", token="token-invalido")
    verificar("me com token invalido retorna 401", status == 401)

    status, _ = chamar("POST", "/auth/login", {"email": email, "password": "senha-errada"})
    verificar("login com senha errada retorna 401", status == 401)

    status, body = chamar("POST", "/auth/login", {"email": email, "password": senha})
    verificar("login retorna 200", status == 200)
    refresh_antigo = cookie_refresh()

    status, body = chamar("POST", "/auth/refresh")
    verificar("refresh retorna 200", status == 200)
    verificar("refresh rotaciona o cookie", cookie_refresh() not in (None, refresh_antigo))
    verificar("refresh devolve novo access_token", bool(body.get("access_token")))
    access_token = body.get("access_token", "")

    status, _ = chamar("GET", "/auth/me", token=access_token)
    verificar("me funciona com o token renovado", status == 200)

    status, _ = chamar("POST", "/auth/logout")
    verificar("logout retorna 200", status == 200)
    verificar("logout limpa o cookie", not cookie_refresh())

    status, _ = chamar("POST", "/auth/refresh")
    verificar("refresh apos logout retorna 401", status == 401)

    status, body = chamar("POST", "/auth/recuperar-senha", {"email": email})
    verificar("recuperar-senha retorna 200", status == 200)
    _, body_inexistente = chamar(
        "POST", "/auth/recuperar-senha", {"email": f"inexistente-{uuid4().hex[:8]}@example.com"}
    )
    verificar("recuperar-senha nao revela existencia do email", body == body_inexistente)

    status, _ = chamar("POST", "/auth/redefinir-senha", {"token": "invalido", "new_password": senha})
    verificar("redefinir-senha com token invalido retorna 400", status == 400)

    print(f"\nUsuario criado: {email} / {senha}")
    encerrar()


if __name__ == "__main__":
    main()

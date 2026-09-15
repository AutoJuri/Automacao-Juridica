"""Smoke test manual da redefinição de senha e do rate limiting.

Enquanto não há provedor de e-mail, o token de redefinição só existe no log do
servidor — por isso o teste roda em duas etapas:

1. `python scripts/smoke_reset.py preparar` cria um usuário e dispara o pedido
   de redefinição; copie o token do log do servidor.
2. `python scripts/smoke_reset.py validar <token> <email> <senha_atual>`
   valida o restante do fluxo.
"""

import sys
from uuid import uuid4

from smoke_auth import chamar, encerrar, verificar

SENHA_INICIAL = "SenhaForte123!"
SENHA_NOVA = "NovaSenhaForte456!"


def preparar() -> None:
    email = f"reset-{uuid4().hex[:12]}@example.com"

    status, _ = chamar(
        "POST", "/auth/cadastro", {"name": "Reset", "email": email, "password": SENHA_INICIAL}
    )
    verificar("cadastro retorna 201", status == 201)

    status, _ = chamar("POST", "/auth/recuperar-senha", {"email": email})
    verificar("recuperar-senha retorna 200", status == 200)

    print(f"\nCopie o token do log do servidor e rode:")
    print(f'  python scripts/smoke_reset.py validar <token> "{email}" "{SENHA_INICIAL}"')
    encerrar()


def validar(token: str, email: str, senha_atual: str) -> None:
    status, _ = chamar(
        "POST", "/auth/redefinir-senha", {"token": token, "new_password": SENHA_NOVA}
    )
    verificar("redefinir-senha com token valido retorna 200", status == 200)

    status, _ = chamar(
        "POST", "/auth/redefinir-senha", {"token": token, "new_password": SENHA_NOVA}
    )
    verificar("token de redefinicao e de uso unico", status == 400)

    status, _ = chamar("POST", "/auth/login", {"email": email, "password": senha_atual})
    verificar("senha antiga nao autentica mais", status == 401)

    status, _ = chamar("POST", "/auth/login", {"email": email, "password": SENHA_NOVA})
    verificar("nova senha autentica", status == 200)

    status, body = chamar("POST", "/auth/recuperar-senha", {"email": email})
    verificar("rate limit de recuperar-senha dispara 429", status == 429)
    verificar("429 nao revela o limite configurado", "hour" not in str(body).lower())

    encerrar()


if __name__ == "__main__":
    if sys.argv[1:2] == ["preparar"]:
        preparar()
    elif sys.argv[1:2] == ["validar"]:
        validar(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
        sys.exit(2)

"""Validadores Pydantic reutilizados por mais de um schema.

Hoje só a regra de bytes da senha (compartilhada entre `schemas/auth.py` e
`schemas/credentials.py`), mas evita duplicar a mesma constante/validator em
cada schema novo que também lidar com senha.
"""

# 72 é o teto do bcrypt, mas em BYTES (UTF-8), não em caracteres — um
# emoji ou acento pode ocupar de 2 a 4 bytes. `max_length` do Pydantic conta
# caracteres, então uma senha com 72 caracteres multibyte passaria pelo
# schema e só explodiria dentro de hash_password. O validator abaixo fecha
# essa lacuna com um 422 claro em vez de um 500.
SENHA_MIN = 8
SENHA_MAX = 72


def valida_bytes_da_senha(v: str) -> str:
    if len(v.encode("utf-8")) > SENHA_MAX:
        raise ValueError(f"Senha excede o limite de {SENHA_MAX} bytes")
    return v

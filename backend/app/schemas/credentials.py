"""Schemas de entrada e saída das rotas de credenciais e OAuth2 de e-mail.

Nenhum schema de resposta expõe CPF real, senha ou os campos `*_encrypted` —
o único CPF que sai daqui é a versão mascarada (`cpf_mascarado`).
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.cpf import is_valid_cpf, normalize_cpf
from app.core.validators import SENHA_MAX, SENHA_MIN, valida_bytes_da_senha


class EsajCredentialCreateSchema(BaseModel):
    cpf: str = Field(min_length=11, max_length=14)
    senha: str = Field(min_length=SENHA_MIN, max_length=SENHA_MAX)

    @field_validator("cpf")
    @classmethod
    def _valida_cpf(cls, v: str) -> str:
        normalizado = normalize_cpf(v)
        if not is_valid_cpf(normalizado):
            raise ValueError("CPF inválido")
        return normalizado

    @field_validator("senha")
    @classmethod
    def _valida_senha_bytes(cls, v: str) -> str:
        return valida_bytes_da_senha(v)


class CredentialStatusSchema(BaseModel):
    cadastrado: bool
    tribunal: str | None = None
    cpf_mascarado: str | None = None
    email_provider: str | None = None
    email_conectado: bool = False
    last_validated_at: datetime | None = None
    is_active: bool | None = None
    # Um dos `SESSION_STATUSES` (ver app.models.tribunal), ou `None` se
    # nenhuma validação de login jamais foi disparada para esta credencial.
    session_status: str | None = None
    # `status=ativo` mas `expires_at` já passou (ou cookie nulo). O cookie
    # em si nunca sai da API — só este booleano para a UI mostrar Revalidar.
    sessao_expirada: bool = False
    # Playwright deste processo está rodando AGORA para este advogado
    # (`_VALIDACOES_EM_ANDAMENTO`). Distinto de `session_status=reauth_pendente`,
    # que também significa "cookie inválido, falta reauth" depois de um
    # ciclo de coleta — sem este flag a UI entra em polling eterno.
    validacao_em_andamento: bool = False


class AuthorizeUrlSchema(BaseModel):
    authorize_url: str


class ProviderSugeridoSchema(BaseModel):
    """Sugestão de provedor (Etapa 9) a partir do domínio do e-mail de
    login da plataforma — nunca decide sozinha, só simplifica o card de
    conexão. `None` quando não há como sugerir com confiança."""

    provider: str | None = None

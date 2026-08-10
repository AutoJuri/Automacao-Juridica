"""Models SQLAlchemy.

Importar tudo aqui garante que `Base.metadata` esteja completo quando o
Alembic roda o autogenerate.
"""

from app.db.base import Base
from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.models.job_log import JobLog
from app.models.movimentacao import Movimentacao
from app.models.notification import Notification
from app.models.password_reset_token import PasswordResetToken
from app.models.processo import Processo
from app.models.refresh_token import RefreshToken
from app.models.tribunal import TribunalCredential, TribunalSession
from app.models.user import User

__all__ = [
    "Audiencia",
    "Base",
    "Intimacao",
    "JobLog",
    "Movimentacao",
    "Notification",
    "PasswordResetToken",
    "Processo",
    "RefreshToken",
    "TribunalCredential",
    "TribunalSession",
    "User",
]

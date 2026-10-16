"""Cliente do Google Drive (ADR-022), em httpx puro.

O token só existe descriptografado dentro destas funções. Nunca vai ao log,
à resposta da API nem ao frontend (a única saída é `token_para_picker`, de
vida curta e só com `drive.file`).

Com o escopo `drive.file` o Google responde 404 para o que a plataforma não
criou e a pessoa não escolheu no seletor. Por isso 404 vira "recurso ausente".
"""

import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DecriptografiaError, decrypt_secret, encrypt_secret
from app.models.drive_conexao import DriveConexao
from app.models.drive_pasta import DrivePasta
from app.services import oauth_google_drive
from app.services.oauth_common import OAuthTokenExchangeError

logger = logging.getLogger(__name__)

API = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
CAMPOS_ARQUIVO = "id,name,mimeType,size,trashed"
MIME_PASTA = "application/vnd.google-apps.folder"
NOME_PASTA_RAIZ = "AdvogAtiva"

TIMEOUT_METADADOS = 10.0
TIMEOUT_TRANSFERENCIA = 60.0
# Renova um pouco antes de vencer, para não gastar um 401 à toa.
MARGEM_RENOVACAO = timedelta(seconds=60)


class DriveGoogleError(Exception):
    """Falha ao falar com o Google Drive."""


class DriveDesconectadoError(DriveGoogleError):
    """Sem conexão, ou o Google recusou renovar o acesso (revogado)."""


class DriveRecursoAusenteError(DriveGoogleError):
    """O Google não enxerga mais o arquivo ou a pasta."""


def url_do_arquivo(google_file_id: str) -> str:
    """Link público do padrão do Drive. Quem abre ainda precisa de acesso."""
    return f"https://drive.google.com/file/d/{quote(google_file_id, safe='')}/view"


def _expira_em(payload: dict) -> datetime | None:
    bruto = payload.get("expires_at")
    if not isinstance(bruto, str):
        return None
    try:
        valor = datetime.fromisoformat(bruto)
    except ValueError:
        return None
    return valor if valor.tzinfo else valor.replace(tzinfo=UTC)


class ClienteDrive:
    def __init__(self, db: AsyncSession, conexao: DriveConexao) -> None:
        self.db = db
        self.conexao = conexao

    # --- token -----------------------------------------------------------

    def _payload(self) -> dict:
        try:
            return json.loads(decrypt_secret(self.conexao.token_encrypted))
        except (DecriptografiaError, ValueError) as exc:
            raise DriveDesconectadoError("TokenIlegivel") from exc

    def payload_atual(self) -> dict | None:
        """Token atual, ou `None` se estiver ilegível. Uso interno, nunca vai à API."""
        try:
            return self._payload()
        except DriveDesconectadoError:
            return None

    async def _renovar(self, payload: dict) -> dict:
        refresh = payload.get("refresh_token")
        if not refresh:
            raise DriveDesconectadoError("SemRefreshToken")
        try:
            tokens = await oauth_google_drive.refresh_access_token(refresh)
        except OAuthTokenExchangeError as exc:
            raise DriveDesconectadoError("RefreshRecusado") from exc
        novo = oauth_google_drive.montar_payload(tokens, anterior=payload)
        self.conexao.token_encrypted = encrypt_secret(json.dumps(novo))
        await self.db.commit()
        return novo

    async def _access_token(self, *, margem: timedelta = MARGEM_RENOVACAO) -> str:
        payload = self._payload()
        expira = _expira_em(payload)
        if not payload.get("access_token") or (
            expira is not None and expira <= datetime.now(UTC) + margem
        ):
            payload = await self._renovar(payload)
        return str(payload["access_token"])

    async def token_para_picker(self) -> tuple[str, int]:
        """Token curto para o seletor do Google. Exceção documentada na ADR-022."""
        margem = timedelta(minutes=5)
        token = await self._access_token(margem=margem)
        expira = _expira_em(self._payload())
        restante = int((expira - datetime.now(UTC)).total_seconds()) if expira else 300
        return token, max(restante, 60)

    async def revogar(self) -> None:
        try:
            payload = self._payload()
        except DriveDesconectadoError:
            return
        token = payload.get("refresh_token") or payload.get("access_token")
        if token:
            await oauth_google_drive.revoke_token(str(token))

    # --- chamadas --------------------------------------------------------

    async def _enviar(
        self, metodo: str, url: str, token: str, timeout: float, **kwargs
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {token}", **kwargs.pop("headers", {})}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                return await client.request(metodo, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            logger.warning("Falha de rede no Google Drive (%s)", type(exc).__name__)
            raise DriveGoogleError("RedeIndisponivel") from exc

    async def _requisitar(
        self, metodo: str, url: str, *, timeout: float = TIMEOUT_METADADOS, **kwargs
    ) -> httpx.Response:
        token = await self._access_token()
        resposta = await self._enviar(metodo, url, token, timeout, **kwargs)
        if resposta.status_code == httpx.codes.UNAUTHORIZED:
            payload = await self._renovar(self._payload())
            resposta = await self._enviar(metodo, url, str(payload["access_token"]), timeout, **kwargs)
        if resposta.status_code == httpx.codes.UNAUTHORIZED:
            raise DriveDesconectadoError("AcessoRecusado")
        return resposta

    @staticmethod
    def _checar(resposta: httpx.Response) -> httpx.Response:
        if resposta.status_code == httpx.codes.NOT_FOUND:
            raise DriveRecursoAusenteError("NaoEncontrado")
        if not resposta.is_success:
            logger.warning("Google Drive respondeu %s", resposta.status_code)
            raise DriveGoogleError(f"Status{resposta.status_code}")
        return resposta

    # --- arquivos e pastas -----------------------------------------------

    async def metadados(self, google_file_id: str) -> dict:
        resposta = await self._requisitar(
            "GET",
            f"{API}/{quote(google_file_id, safe='')}",
            params={"fields": CAMPOS_ARQUIVO},
        )
        return self._checar(resposta).json()

    async def _criar_pasta(self, nome: str, pai: str | None = None) -> str:
        corpo: dict = {"name": nome, "mimeType": MIME_PASTA}
        if pai:
            corpo["parents"] = [pai]
        resposta = await self._requisitar("POST", API, params={"fields": "id"}, json=corpo)
        return str(self._checar(resposta).json()["id"])

    async def _pasta_ativa(self, folder_id: str) -> bool:
        try:
            dados = await self.metadados(folder_id)
        except DriveRecursoAusenteError:
            return False
        return not dados.get("trashed") and dados.get("mimeType") == MIME_PASTA

    async def garantir_pasta_raiz(self) -> str:
        if self.conexao.root_folder_id and await self._pasta_ativa(self.conexao.root_folder_id):
            return self.conexao.root_folder_id
        self.conexao.root_folder_id = await self._criar_pasta(NOME_PASTA_RAIZ)
        await self.db.commit()
        return self.conexao.root_folder_id

    async def garantir_pasta(self, pasta: DrivePasta) -> str:
        """Pasta no Google da `DrivePasta`. Recria se a pessoa a apagou no Drive."""
        if pasta.google_folder_id and await self._pasta_ativa(pasta.google_folder_id):
            return pasta.google_folder_id
        raiz = await self.garantir_pasta_raiz()
        pasta.google_folder_id = await self._criar_pasta(pasta.nome, raiz)
        await self.db.commit()
        return pasta.google_folder_id

    async def enviar(self, nome: str, mime: str, conteudo: bytes, pasta_google_id: str) -> dict:
        limite = f"advogativa-{secrets.token_hex(16)}"
        metadados = json.dumps({"name": nome, "parents": [pasta_google_id]}).encode("utf-8")
        corpo = b"".join(
            [
                f"--{limite}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode(),
                metadados,
                f"\r\n--{limite}\r\nContent-Type: {mime}\r\n\r\n".encode(),
                conteudo,
                f"\r\n--{limite}--".encode(),
            ]
        )
        resposta = await self._requisitar(
            "POST",
            UPLOAD,
            timeout=TIMEOUT_TRANSFERENCIA,
            params={"uploadType": "multipart", "fields": CAMPOS_ARQUIVO},
            headers={"Content-Type": f"multipart/related; boundary={limite}"},
            content=corpo,
        )
        return self._checar(resposta).json()

    async def baixar(self, google_file_id: str) -> bytes:
        resposta = await self._requisitar(
            "GET",
            f"{API}/{quote(google_file_id, safe='')}",
            timeout=TIMEOUT_TRANSFERENCIA,
            params={"alt": "media"},
        )
        return self._checar(resposta).content

    async def lixeira(self, google_file_id: str) -> None:
        resposta = await self._requisitar(
            "PATCH",
            f"{API}/{quote(google_file_id, safe='')}",
            json={"trashed": True},
        )
        try:
            self._checar(resposta)
        except DriveRecursoAusenteError:
            return  # já não existe: o resultado é o mesmo

    async def mover(self, google_file_id: str, para: str, de: str | None) -> None:
        params = {"addParents": para, "fields": "id"}
        if de:
            params["removeParents"] = de
        resposta = await self._requisitar(
            "PATCH", f"{API}/{quote(google_file_id, safe='')}", params=params, json={}
        )
        self._checar(resposta)

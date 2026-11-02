"""E-mail transacional da AdvogAtiva via Resend.

Não usa o OAuth do advogado. O log leva o tipo e o id do provedor.
Token, link, chave e destinatário ficam de fora desse log. Sem chave, em
development, o link ainda vai para o log para o fluxo local funcionar.
"""

import asyncio
import html
import logging
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MensagemPlataforma:
    tipo: str
    destinatario: str
    assunto: str
    texto: str
    html: str
    link: str


def _carta(
    *,
    rotulo: str,
    titulo: str,
    paragrafos: list[str],
    botao: str,
    link: str,
    aviso: str,
) -> str:
    """HTML de e-mail em tabela, com CSS na própria tag. Clientes ignoram flex e folha externa."""
    href = html.escape(link, quote=True)
    fonte = "Arial, Helvetica, sans-serif"
    blocos = "".join(
        (
            f'<p style="margin:0 0 14px;font-family:{fonte};font-size:15px;'
            f'line-height:24px;color:#374151;">{html.escape(paragrafo)}</p>'
        )
        for paragrafo in paragrafos
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background:#F3F4F6;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F3F4F6;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;background:#ffffff;border:1px solid #E5E7EB;border-radius:16px;">
          <tr>
            <td style="padding:28px 32px 20px;border-bottom:3px solid #2563EB;">
              <p style="margin:0;font-family:{fonte};font-size:18px;font-weight:700;color:#111827;">AdvogAtiva</p>
              <p style="margin:6px 0 0;font-family:{fonte};font-size:11px;letter-spacing:1.4px;text-transform:uppercase;color:#2563EB;">Secure Hub</p>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px 0;">
              <p style="margin:0;font-family:{fonte};font-size:12px;letter-spacing:1.2px;text-transform:uppercase;color:#6B7280;">{html.escape(rotulo)}</p>
              <h1 style="margin:8px 0 18px;font-family:{fonte};font-size:22px;line-height:30px;font-weight:700;color:#111827;">{html.escape(titulo)}</h1>
              {blocos}
              <table cellpadding="0" cellspacing="0" role="presentation" style="margin:6px 0 18px;">
                <tr>
                  <td bgcolor="#2563EB" style="border-radius:8px;background:#2563EB;">
                    <a href="{href}" style="display:inline-block;padding:12px 22px;font-family:{fonte};font-size:15px;font-weight:700;line-height:20px;color:#ffffff;text-decoration:none;">{html.escape(botao)}</a>
                  </td>
                </tr>
              </table>
              <p style="margin:0;font-family:{fonte};font-size:13px;line-height:20px;color:#6B7280;">Se o botão não abrir, copie este endereço no navegador:<br><a href="{href}" style="color:#2563EB;word-break:break-all;">{href}</a></p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F9FAFB;border-radius:8px;">
                <tr>
                  <td style="padding:14px 16px;font-family:{fonte};font-size:13px;line-height:20px;color:#6B7280;">{html.escape(aviso)}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        <p style="margin:16px 0 0;font-family:{fonte};font-size:12px;line-height:18px;color:#9CA3AF;">Mensagem automática da AdvogAtiva. Não responda este e-mail.</p>
      </td>
    </tr>
  </table>
</body>
</html>"""


def mensagem_redefinicao(destinatario: str, link: str, minutos: int) -> MensagemPlataforma:
    return MensagemPlataforma(
        tipo="redefinicao",
        destinatario=destinatario,
        assunto="Redefinir senha da AdvogAtiva",
        texto=(
            "AdvogAtiva\n\n"
            "Recebemos um pedido para criar uma nova senha na sua conta.\n\n"
            f"O link vale por {minutos} minutos e só pode ser usado uma vez:\n"
            f"{link}\n\n"
            "Se você não fez esse pedido, ignore este e-mail. "
            "A senha atual continua a mesma. A AdvogAtiva não pede a senha por resposta."
        ),
        html=_carta(
            rotulo="Redefinição de senha",
            titulo="Crie uma nova senha",
            paragrafos=[
                "Recebemos um pedido para criar uma nova senha na sua conta da AdvogAtiva.",
                (
                    f"O botão abre a página de redefinição. O link vale por {minutos} minutos "
                    "e só pode ser usado uma vez."
                ),
            ],
            botao="Redefinir senha",
            link=link,
            aviso=(
                "Se você não fez esse pedido, ignore este e-mail. A senha atual continua a mesma. "
                "A AdvogAtiva não pede a senha por resposta."
            ),
        ),
        link=link,
    )


def mensagem_convite(
    destinatario: str,
    nome_organizacao: str,
    papel: str,
    link: str,
) -> MensagemPlataforma:
    nome = " ".join(nome_organizacao.split())
    return MensagemPlataforma(
        tipo="convite",
        destinatario=destinatario,
        assunto=f"Convite para {nome}",
        texto=(
            "AdvogAtiva\n\n"
            f"Você foi convidado para {nome} como {papel}.\n\n"
            "O link vale por 7 dias. Se ainda não tiver conta, crie uma com este mesmo e-mail:\n"
            f"{link}\n\n"
            "Se você não esperava este convite, ignore o e-mail. Nada muda na sua conta."
        ),
        html=_carta(
            rotulo="Convite de escritório",
            titulo=f"Entre em {nome}",
            paragrafos=[
                f"Você foi convidado para {nome} como {papel}.",
                (
                    "O botão abre o convite. Se ainda não tiver conta, dá para criar uma "
                    "com este mesmo e-mail. O link vale por 7 dias."
                ),
            ],
            botao="Ver convite",
            link=link,
            aviso=(
                "Se você não esperava este convite, ignore o e-mail. Nada muda na sua conta."
            ),
        ),
        link=link,
    )


def _id_da_resposta(resposta: object) -> str:
    if isinstance(resposta, dict):
        valor = resposta.get("id")
    else:
        valor = getattr(resposta, "id", None)
    return str(valor) if valor else ""


def _enviar(api_key: str, remetente: str, mensagem: MensagemPlataforma) -> str:
    import resend

    resend.api_key = api_key
    resposta = resend.Emails.send(
        {
            "from": remetente,
            "to": [mensagem.destinatario],
            "subject": mensagem.assunto,
            "html": mensagem.html,
            "text": mensagem.texto,
        }
    )
    return _id_da_resposta(resposta)


async def entregar(mensagem: MensagemPlataforma) -> None:
    """Envia ou, sem provedor, registra o fallback. Nunca propaga a falha."""
    settings = get_settings()
    chave = settings.resend_api_key.strip()
    if not chave:
        if settings.is_development:
            logger.warning(
                "Link de %s gerado para entrega local: %s",
                mensagem.tipo,
                mensagem.link,
            )
            return
        logger.warning("Provedor de e-mail ausente ao enviar %s", mensagem.tipo)
        return

    remetente = settings.email_from.strip()
    if not remetente:
        logger.warning("Remetente de e-mail ausente ao enviar %s", mensagem.tipo)
        return

    try:
        ident = await asyncio.to_thread(_enviar, chave, remetente, mensagem)
    except Exception as exc:
        logger.warning("Falha ao enviar e-mail %s: %s", mensagem.tipo, type(exc).__name__)
        return

    logger.info("E-mail %s aceito pelo provedor id=%s", mensagem.tipo, ident)

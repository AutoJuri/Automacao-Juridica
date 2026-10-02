import DOMPurify from 'dompurify'

/**
 * Sanitiza HTML antes de entrar no editor (TipTap) — todo conteúdo que vem
 * da IA (mesmo em modo stub, ADR-016) passa por aqui antes de
 * `editor.commands.setContent(...)` (`security.mdc` §7: nunca
 * `dangerouslySetInnerHTML`/HTML de terceiro sem sanitizar).
 *
 * Lista de tags restrita ao que o editor e os providers de LLM produzem.
 * Atributos ficam de fora (`style` inclusive): CSS inline de um HTML de
 * terceiro não entra no editor.
 */
export function sanitizarHtmlMinuta(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'u', 's', 'span', 'br'],
    ALLOWED_ATTR: [],
  })
}

# Módulo: Elaboração

> Última atualização: 2026-10-15
> Camada: Backend / Frontend

---

## O que este módulo faz

Guarda a capa de cada peça que o advogado começou a elaborar e mostra isso em `/elaboracoes`: o que já está em andamento e os processos que ainda não têm nenhuma elaboração. O texto que aparece no editor continua no navegador. No servidor, a IA (ADR-016) já gera e edita versões cifradas; a tela do hall ainda não chama esses endpoints.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/elaboracao.py` | Tabela `elaboracoes` e a lista de peças aceitas |
| `backend/app/schemas/elaboracao.py` | Entrada com `extra=forbid` e respostas explícitas |
| `backend/app/services/elaboracoes.py` | Lista, criação, reabertura, atualização e exclusão, sempre por `user_id` |
| `backend/app/api/elaboracoes.py` | Rotas da capa em `/elaboracoes` |
| `backend/app/api/elaboracao.py` | Rotas da IA: fatos, gerar, editar, estilo, versões e sugestão de peça |
| `backend/app/services/elaboracao.py` | Cifra o texto e chama o adapter de LLM |
| `backend/app/services/llm/` | `stub`, OpenRouter e Anthropic |
| `frontend/src/features/elaboracao/ElaboracoesPage.tsx` | Hall: Em andamento e Para começar |
| `frontend/src/features/elaboracao/ElaboracaoPage.tsx` | Minuta aberta pelo id da elaboração |
| `frontend/src/features/elaboracao/elaboracao.manual.ts` | Adapta os dados digitados para o formato da ficha |
| `frontend/src/routes/elaboracoes.lazy.tsx` | Página da seção, carregada à parte |
| `frontend/src/routes/elaboracao.$elaboracaoId.tsx` | Rota da minuta |

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/elaboracoes` | Elaborações do usuário, da mais recente à mais antiga, no máximo 100 | Sim |
| GET | `/elaboracoes/a-iniciar` | Processos do usuário sem nenhuma elaboração. Página fixa de 12 (`offset`, `q`) | Sim |
| POST | `/elaboracoes` | Cria a capa. Se a mesma peça já existe naquele processo, devolve a existente (200, não 201) | Sim |
| GET | `/elaboracoes/{id}` | Capa de uma elaboração | Sim |
| PATCH | `/elaboracoes/{id}` | Troca a peça, edita os dados manuais ou só renova `updated_at` | Sim |
| DELETE | `/elaboracoes/{id}` | Remove a capa. O rascunho local é limpo no cliente | Sim |
| PATCH | `/elaboracoes/{id}/fatos` | Grava os fatos extras cifrados | Sim |
| POST | `/elaboracoes/{id}/gerar` | Primeira versão da minuta via LLM. 30/hora | Sim |
| POST | `/elaboracoes/{id}/editar` | Chat ou grifo sobre a última versão. 30/hora | Sim |
| POST | `/elaboracoes/{id}/estilo` | Extrai perfil de estilo de um texto. 30/hora | Sim |
| GET | `/elaboracoes/{id}/versoes` | Histórico cifrado, já decriptado para o dono | Sim |
| GET | `/elaboracoes/sugestao-peca` | Palpite de peça para um processo. 30/hora | Sim |

> Toda rota usa `Depends(get_current_user)`.
> `user_id` nunca é aceito via body, path ou query — sempre vem do JWT.
> Elaboração ou processo de outra pessoa responde 404.

---

## Funções e hooks públicos

| Nome | Arquivo | Descrição |
|---|---|---|
| `useElaboracoes` | `elaboracoes.queries.ts` | Lista em andamento |
| `useProcessosParaIniciar` | `elaboracoes.queries.ts` | Páginas de processos sem elaboração |
| `useCriarElaboracao` | `elaboracoes.queries.ts` | Cria a partir de um processo ou dos dados manuais |
| `processoDeDadosManuais` | `elaboracao.manual.ts` | Ficha vazia de listas, preenchida com o que foi digitado |
| `juntarPorId` | `elaboracoes.pagina.ts` | Acrescenta a página seguinte sem repetir card |
| `lerVersoesDaElaboracao` | `elaboracao.versoes.ts` | Lê a chave nova e, se estiver vazia, a chave antiga (processo + peça) |

---

## Padrões seguidos neste módulo

- **Autenticação:** `Depends(get_current_user)` em toda rota
- **Ownership:** `WHERE user_id = current_user.id` no banco. Recurso de outra pessoa é 404, nunca 403
- **Resposta:** `ElaboracaoCardSchema`, `ElaboracaoDetalheSchema` e `PaginaProcessosParaIniciarSchema` — nunca o ORM
- **Validação:** `extra="forbid"` na entrada. A peça tem de estar na lista conhecida. Processo e dados manuais não vêm juntos
- **Página:** o cliente não escolhe o tamanho. "Para começar" devolve 12
- **Texto:** nomes de partes são texto do React. Nada de HTML vindo da capa
- **Minuta:** HTML e versões ficam em `localStorage`, chave `advogativa.minuta.versoes.elaboracao.{id}`. Na tela, o mesmo documento é desenhado em folhas A4 (margem de 2,54 cm). A folha seguinte aparece quando o texto não cabe; a quebra de página (Ctrl+Enter) força uma folha nova no cursor. O contador fica no rodapé da minuta.

---

## Modelo de dados relacionado

`elaboracoes` pertence ao usuário. `processo_id` é nulo quando os dados foram digitados. Com processo, os campos manuais ficam nulos e só pode existir uma linha por `(user_id, processo_id, peca)`.

```python
class Elaboracao(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "elaboracoes"
    user_id: Mapped[uuid.UUID]
    processo_id: Mapped[uuid.UUID | None]
    peca: Mapped[str]
    titulo: Mapped[str | None]
```

Constraints: `ck_elaboracoes_origem` (processo ou título) e `ck_elaboracoes_manual_so_sem_processo`. Índice único parcial `uq_elaboracoes_user_processo_peca`.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| `auth` | `user_id` do JWT em toda operação |
| `processos` | A elaboração com processo lê a ficha em `GET /processos/{id}` e só cria se o processo for do mesmo usuário |

---

## O que NÃO fazer aqui

- ❌ Não aceitar `user_id` no corpo
- ❌ Não devolver 403 para elaboração de outra pessoa — a resposta é 404
- ❌ Não gravar o HTML da minuta nesta tabela
- ❌ Não chamar provedor de IA nas rotas da capa (`elaboracoes.py`). Quem chama é `api/elaboracao.py`
- ❌ Não deixar o cliente escolher o tamanho da página de "Para começar"
- ❌ Não criar uma segunda elaboração da mesma peça no mesmo processo
- ❌ Não misturar `processo_id` com os campos manuais na mesma linha

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-10-08 | Primeira capa no servidor: hall, elaboração sem processo e minuta por id (ADR-021) |
| 2026-10-09 | Nova elaboração abre a minuta direto; os dados do processo são preenchidos nos campos da esquerda |
| 2026-10-09 | A minuta é um documento só, desenhado em folhas A4. A folha seguinte aparece quando o texto não cabe; a quebra de página força uma folha nova |
| 2026-10-13 | Ficou decidido que o anexo da elaboração e a minuta exportada vão para a pasta do processo no Google Drive (ADR-022). Esta tela ainda guarda o arquivo só no navegador |
| 2026-10-13 | O anexo da peça modelo ganhou "Guardar no Drive" (`GuardarNoDrive.tsx`): o `File` fica em memória e só sai do navegador por clique, para a pasta escolhida (a pasta ligada ao processo vem sugerida), com `origem=elaboracao`. Sem Google conectado, a tela só aponta para `/drive`. A minuta exportada ainda não vai ao Drive. A IA continua sem ler o anexo |
| 2026-10-15 | A branch da IA entrou sem substituir a capa. Fatos, estilo e versões ficam cifrados. A tela ainda não dispara gerar/editar |

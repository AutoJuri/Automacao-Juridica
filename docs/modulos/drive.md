# Módulo: Drive

> Última atualização: 2026-10-13
> Camada: Backend / Frontend
> Status: pastas livres e integração com o Google Drive implementadas. Falta só a configuração do Google Cloud (credenciais) e o teste com a conta real.

---

## O que este módulo faz

É o cofre de PDF e Word do advogado. A pessoa cria pastas livres, liga cada uma a um processo se fizer sentido e, depois de conectar a conta Google, guarda arquivos nelas. O arquivo mora no Google Drive dela; o Postgres guarda só a ficha (ADR-022).

Três jeitos de um arquivo entrar numa pasta:

1. **Enviar:** arrasta ou escolhe no computador. O navegador manda ao nosso backend, que valida e grava no Drive da pessoa.
2. **Escolher do Google Drive:** abre o seletor do Google e a plataforma vincula o arquivo que já existe lá. Nada é copiado.
3. **Guardar da elaboração:** na tela da elaboração, o anexo da peça modelo vai para uma pasta, por clique. A minuta exportada (Word/PDF) fica para outra etapa.

Sem a conta Google conectada, as pastas funcionam normalmente; só o envio e o seletor ficam indisponíveis, com o motivo na tela.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/drive_pasta.py` | `DrivePasta`: `user_id`, `nome` (até 120), `processo_id` opcional, `google_folder_id` (criada sob demanda no Google) |
| `backend/app/models/drive_conexao.py` | `DriveConexao`: uma por usuário. `token_encrypted` (BYTEA, AES-256-GCM) e `root_folder_id` da pasta "AdvogAtiva" |
| `backend/app/models/drive_arquivo.py` | `DriveArquivo`: a ficha. `google_file_id`, `nome`, `mime_type`, `tamanho`, `origem` (`upload`, `drive`, `elaboracao`), `ausente_no_google`. Único por (`pasta_id`, `google_file_id`) |
| `backend/app/db/migrations/versions/b4d8f1a6c3e2_cria_drive_pastas.py` | Cria `drive_pastas` |
| `backend/app/db/migrations/versions/c7e2a9d4b1f8_cria_drive_google.py` | Cria `drive_conexoes` e `drive_arquivos`; adiciona `drive_pastas.google_folder_id` |
| `backend/app/schemas/drive.py` | Schemas de pasta, de status, de token do seletor e de arquivo. Entradas com `extra=forbid` |
| `backend/app/services/drive.py` | Regras das pastas. `total_arquivos` vem de contagem real |
| `backend/app/services/oauth_google_drive.py` | URL de consentimento (`drive.file`, `access_type=offline`), troca de código, refresh e revogação. httpx puro |
| `backend/app/services/drive_google.py` | `ClienteDrive`: fala com a API do Drive (pasta, envio, download, lixeira, mover). Renova o token uma vez em 401 |
| `backend/app/services/drive_arquivos.py` | Regras de arquivo e de conexão: listar, enviar, vincular, baixar, mover, excluir, desconectar |
| `backend/app/core/arquivos_drive.py` | Validação: lista de extensões, assinatura (magic bytes), 25 MB, nome saneado |
| `backend/app/api/drive.py` | Rotas `/drive/pastas` e `/drive/arquivos` |
| `backend/app/api/drive_google.py` | Rotas `/drive/google` (conexão e token do seletor) |
| `frontend/src/features/drive/GoogleDriveAviso.tsx` | Cartão de conexão: Conectar, Desconectar (dois cliques), resultado de `?google=` |
| `frontend/src/features/drive/ArquivosPasta.tsx` e `ArquivoLinha.tsx` | Lista de arquivos, envio (clique e arrasto), seletor do Google, baixar, abrir no Drive, mover, excluir |
| `frontend/src/features/drive/drive.picker.ts` | Carrega o script do Google só no clique e abre o seletor com o token curto |
| `frontend/src/features/drive/drive.errors.ts` | Mensagem para a tela a partir do erro da API |
| `frontend/src/features/elaboracao/GuardarNoDrive.tsx` | "Guardar no Drive" no anexo da peça modelo |
| `frontend/src/features/drive/*` (restante) | Páginas, cartões, diálogo de pasta, tipos, constantes, API, queries e formato |

---

## Rotas

Todas exigem login. Pasta ou arquivo de outra pessoa responde 404.

| Método | Rota | O que faz |
|---|---|---|
| GET | `/drive/pastas` | Lista as pastas (limite 200), com `total_arquivos` real |
| POST | `/drive/pastas` | Cria. Corpo: `nome`, `processo_id` opcional |
| GET | `/drive/pastas/{id}` | Uma pasta |
| PATCH | `/drive/pastas/{id}` | Renomeia e liga/desliga o processo |
| DELETE | `/drive/pastas/{id}` | Apaga a pasta e as fichas. **Não mexe em nada no Google** |
| GET | `/drive/google/status` | `configurado`, `picker_configurado`, `conectado` |
| GET | `/drive/google/authorize` | Devolve a URL de consentimento (`state` assinado) |
| GET | `/drive/google/callback` | Pública. Troca o código e redireciona para `/drive?google=conectado\|erro\|escopo` |
| DELETE | `/drive/google` | Revoga no Google e apaga a conexão. As fichas ficam |
| POST | `/drive/google/picker-token` | Token de acesso curto para o seletor (ver exceção abaixo). `Cache-Control: no-store` |
| GET | `/drive/pastas/{id}/arquivos` | Lista os arquivos da pasta |
| POST | `/drive/pastas/{id}/arquivos` | Envio (multipart: `arquivo`, `origem` = `upload` ou `elaboracao`). 413 acima de 25 MB |
| POST | `/drive/pastas/{id}/arquivos/vincular` | Vincula um arquivo escolhido no seletor (`google_file_id`) |
| GET | `/drive/arquivos/{id}/conteudo` | Baixa o byte pelo backend (`attachment`, `nosniff`, `no-store`) |
| PATCH | `/drive/arquivos/{id}` | Move para outra pasta (`pasta_id`) |
| DELETE | `/drive/arquivos/{id}` | Exclui (regra abaixo) |

---

## Como a pessoa usa

1. Em `/drive`, clica em **Conectar Google Drive**. O Google mostra o consentimento (só `drive.file`). Ao voltar, o cartão fica verde.
2. Cria uma pasta (livre, processo opcional) e abre.
3. Arrasta um PDF ou Word, ou usa **Enviar arquivo**. Ou usa **Escolher do Google Drive** para apontar um arquivo que já tem lá.
4. Na lista: **Baixar**, **Abrir no Drive** (aba nova), **Mover para…** outra pasta, **Excluir** (dois cliques). Dá para ordenar por nome (A–Z ou Z–A) ou pela data em que o arquivo entrou na pasta, filtrar por tipo (PDF, Word, texto, imagem), buscar pelo nome e alternar entre lista e grade. A busca também existe na lista de pastas. A escolha da visualização fica no navegador. O ícone muda de cor conforme o tipo, na lista e na grade.
5. Na elaboração, o anexo da peça modelo ganha **Guardar no Drive**, com a pasta do processo já escolhida se houver.

Na pasta da plataforma aparece, na conta Google dela, uma pasta **AdvogAtiva** e, dentro, uma pasta por registro de `drive_pastas`. Essas pastas são criadas só quando o primeiro arquivo vai.

---

## Regras que o código garante

- **Escopo mínimo:** `drive.file`. O Google responde 404 para arquivo que a plataforma não criou e que a pessoa não escolheu. Por isso o seletor é obrigatório para arquivos antigos.
- **Excluir arquivo:**
  - `upload` e `elaboracao` (a plataforma criou): vai para a **lixeira** do Google e a ficha some.
  - `drive` (a pessoa escolheu): some **só a ficha**. O arquivo dela nunca é tocado.
- **Mover arquivo:** `upload`/`elaboracao` mudam de pasta no Google; `drive` muda só a ficha.
- **Excluir pasta:** apaga a ficha da pasta e dos arquivos. Nunca apaga nem move nada no Google.
- **Arquivo sumiu do Google:** o download recebe 404 do Google, a ficha vira `ausente_no_google` e a tela avisa, em vez de fingir que o arquivo existe.
- **Desconectar:** revoga o token no Google e apaga a conexão. Fichas e arquivos permanecem.
- **Validação do envio:** extensões `.pdf .doc .docx .odt .txt .rtf .png .jpg .jpeg`, assinatura conferida, executáveis recusados, vazio recusado, até 25 MB, nome saneado. Tudo revalidado no backend; o frontend só antecipa o aviso.
- **Limites:** envio 60/hora, token do seletor 30/hora, autorização e callback com o limite padrão de OAuth.

---

## O que o banco guarda

- `drive_pastas`: `id`, `user_id`, `nome`, `processo_id` (SET NULL), `google_folder_id`, datas.
- `drive_conexoes`: `user_id` único (CASCADE), `token_encrypted` (access + refresh + validade + escopo, AES-256-GCM), `root_folder_id`.
- `drive_arquivos`: ficha do arquivo. Sem o conteúdo. `ausente_no_google` marca o que o Google não tem mais.
- Nenhum token, e-mail da conta ou id interno do Google sai nas respostas. O link "Abrir no Drive" é montado como `https://drive.google.com/file/d/{id}/view` e não carrega segredo.

---

## Exceção documentada: token curto no navegador

O seletor do Google roda no navegador e precisa de um token. É a única vez em que algo do Google chega ao frontend:

- é o **access token** de `drive.file`, com minutos de vida; o refresh token nunca sai do backend;
- vem de `POST /drive/google/picker-token` (autenticado, limitado, `no-store`);
- fica só em memória durante a abertura do seletor; não vai para store, `localStorage` nem log;
- o script `apis.google.com/js/api.js` só é carregado quando a pessoa clica no botão;
- a chave de API e o número do projeto chegam na mesma resposta (não são `VITE_*`).

Decisão registrada na ADR-022.

---

## Padrões seguidos neste módulo

- **Autenticação:** `Depends(get_current_user)` em toda rota, exceto o callback (o `state` assinado diz de quem é o código).
- **Ownership:** `WHERE user_id = current_user.id`. Recurso de outra pessoa é 404.
- **Entrada:** `extra=forbid`; `user_id` e `organization_id` no corpo respondem 422.
- **Resposta:** schema Pydantic explícito, nunca o ORM.
- **Token do Drive:** AES-256-GCM no banco, descriptografado só em memória, nunca logado. Falha no callback nunca expõe o motivo na URL.
- **httpx puro**, sem SDK do Google. O ponto único de rede é `ClienteDrive._enviar`, que os testes substituem.
- **Frontend:** `beforeLoad` e carregando no arquivo da rota, componente no `lazy`. Logout limpa `DRIVE_QUERY_KEY`.

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| `auth` | `user_id` do JWT e o `state` assinado do OAuth |
| `processos` | Vínculo opcional da pasta e busca do seletor de processo |
| `elaboracao` | O anexo da peça modelo vai para uma pasta por clique (`origem=elaboracao`) |
| `credenciais-esaj-email` | Mesmo padrão de token criptografado e de `state`. O token do Gmail não é reutilizado |

---

## O que NÃO fazer aqui

- ❌ Não gravar PDF ou Word no Postgres nem num bucket
- ❌ Não reusar o token `gmail.readonly`
- ❌ Não pedir `drive.readonly` nem `drive`
- ❌ Não devolver o refresh token nem o access token em nenhuma resposta além do `picker-token`
- ❌ Não guardar o token do seletor em `localStorage`, store ou log
- ❌ Não apagar nem mover no Google um arquivo de origem `drive`
- ❌ Não apagar a pasta do Google ao excluir a pasta da plataforma
- ❌ Não aceitar `user_id` no corpo, na query ou no path
- ❌ Não devolver 403 para recurso de outra pessoa; a resposta é 404
- ❌ Não logar token, nome de arquivo com dado de cliente além do necessário, nem o byte
- ❌ Não tratar a lista como segunda cópia que possa divergir
- ❌ Não compartilhar a pasta entre membros do escritório nesta etapa
- ❌ Não fazer a IA ler o arquivo só porque ele foi ao Drive
- ❌ Não criar pasta dentro de pasta sem decisão nova

---

## Em aberto

- Enviar a minuta exportada (Word/PDF) da elaboração para a pasta.
- Prévia de PDF dentro da tela, ou só abrir no Drive.
- Envio de até 25 MB passa pela memória do backend; se virar problema, trocar por envio resumível direto ao Google.
- OneDrive e R2 ficam de fora (ADR-022).
- Em modo de teste no Google Cloud, o refresh token expira em 7 dias; publicar o app antes de usar com clientes.

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-10-13 | Desenho do cofre: byte no Google Drive, ficha no Postgres, ida e volta com a elaboração (ADR-022) |
| 2026-10-13 | Tela do Drive antes do Google: `drive_pastas`, rotas `/drive/pastas`, páginas `/drive` e `/drive/$pastaId` |
| 2026-10-13 | Integração com o Google Drive: conexão OAuth (`drive.file`), envio, seletor, download, mover, excluir, `total_arquivos` real e "Guardar no Drive" na elaboração. Migration `c7e2a9d4b1f8` |
| 2026-10-14 | Ordenação (nome e data de entrada), filtro por tipo, busca por nome (pastas e arquivos) e visualização em lista ou grade, só no navegador |

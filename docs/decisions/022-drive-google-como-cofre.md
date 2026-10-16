# ADR-022: O cofre do Drive mora no Google Drive do advogado

**Data:** 2026-10-13
**Status:** Aceito. Pastas e integração com o Google Drive implementadas (2026-10-13). Falta a configuração do projeto no Google Cloud e o teste com a conta real

---

## Contexto

`/drive` era uma área autenticada vazia (ADR-014). O advogado precisa de um cofre para PDF e Word: pastas que ele organiza do jeito dele, documentos que ele já usa e o que sair da elaboração. A peça modelo da minuta (`SeletorPecaEspecifica`) ficava só no navegador, com teto de 5 MB, e não ia ao servidor.

O e-mail Google já conectado usa `gmail.readonly` e serve apenas ao código do e-SAJ. Esse consentimento não autoriza arquivo.

Guardar o PDF no Postgres, ou abrir um bucket (Cloudflare R2 ou equivalente) antes de precisar, faria a plataforma pagar e responder pelo arquivo. O advogado já tem conta Google com cota própria.

## Decisão

- O byte do arquivo fica no Google Drive da pessoa. A plataforma é a estante: cria pasta, envia, puxa e lista. Não há segunda cópia no nosso banco nem num bucket.
- O Postgres guarda só a ficha: usuário, pasta, id do arquivo no Google, nome, tipo, tamanho e origem. Sem isso, o Google não sabe qual pasta é de qual processo.
- As pastas são livres. A pessoa cria, nomeia, edita e apaga a pasta que quiser, e liga a um processo apenas quando fizer sentido. Há um nível só, sem pasta dentro de pasta.
- O servidor cria na conta dela uma pasta AdvogAtiva e, dentro, uma pasta para cada registro de `drive_pastas`, só quando o primeiro arquivo vai. O arquivo enviado vai ao Drive e aparece na mesma tela. Mover arquivo entre pastas muda a pasta no Google quando a plataforma criou o arquivo.
- O caminho inverso usa o seletor do Google: um PDF que já está no Drive pode ser apontado e vinculado à pasta. Aí ele entra na lista da plataforma, com origem `drive`.
- Da elaboração, vai o **anexo da peça modelo**, por clique em "Guardar no Drive", para a pasta que a pessoa escolher (a ligada ao processo vem sugerida). A minuta exportada (Word ou PDF) fica para uma etapa futura.
- O escopo é `https://www.googleapis.com/auth/drive.file`. A plataforma vê o que ela criou e o que a pessoa escolheu no seletor. O restante da conta Google fica de fora.
- O consentimento é outro fluxo OAuth2, separado do Gmail. O token segue a regra do e-mail: AES-256-GCM, descriptografar só em memória, nunca na resposta e nunca no log.
- O envio sai do navegador para o nosso backend e do backend para a API do Drive. O backend valida extensão, assinatura do arquivo, tamanho (25 MB) e nome antes de falar com o Google.
- A lista é pessoal (`user_id` do JWT), no mesmo critério da elaboração. Arquivo de outra pessoa responde 404.

### Exceção: token curto para o seletor do Google

O seletor (Google Picker) roda no navegador e exige um token de acesso. Esta é a única exceção à regra de que o token do Google não vai ao frontend:

- Só o **access token** de `drive.file`, de vida curta, é entregue. O refresh token nunca sai do backend.
- Vem de `POST /drive/google/picker-token`: autenticado, com limite por hora e `Cache-Control: no-store`.
- No navegador, vive só em memória durante a abertura do seletor. Não vai para store, `localStorage`, `sessionStorage` nem log.
- O script do Google só é carregado quando a pessoa clica em "Escolher do Google Drive".
- A chave de API (restrita por referrer e pela Picker API) e o número do projeto chegam na mesma resposta; não ficam em `VITE_*`.

Sem o seletor, `drive.file` não enxerga arquivos que a plataforma não criou, e o caminho "usar um PDF que já está no meu Drive" não existiria.

### Regras de exclusão

- Excluir arquivo de origem `upload` ou `elaboracao` (criado pela plataforma): vai para a **lixeira** do Google, recuperável por 30 dias, e a ficha some.
- Excluir ou mover arquivo de origem `drive` (escolhido pela pessoa): afeta **só a ficha**. O arquivo dela no Google nunca é apagado nem movido.
- Excluir uma **pasta** da plataforma apaga a pasta e as fichas. **Nunca** apaga nem move nada no Google: os arquivos e a pasta continuam no Drive da pessoa.
- Se o arquivo sumiu do Google, a ficha é marcada `ausente_no_google` na leitura e a tela avisa.
- Desconectar revoga o token e apaga a conexão. Fichas e arquivos permanecem.

## Alternativas consideradas

- **Cloudflare R2 (ou S3) como cofre:** funciona para quem não tem Google e o escritório inteiro compartilha o mesmo lugar. Descartado como base desta etapa — a pessoa passaria a depender de um armazenamento nosso. Pode voltar como cópia ou como caminho para quem usa só Microsoft.
- **Microsoft OneDrive / Word (Graph, `Files.ReadWrite`):** o `.docx` abre no Word e combina com quem já escreve peça assim. Descartado nesta etapa — o desenho fechado foi o Google Drive. OneDrive continua possível depois, com o mesmo papel de cofre, sem mudar a ficha no Postgres.
- **Espelhar o Drive inteiro (`drive.readonly` ou `drive`):** mostraria a conta pessoal. Descartado — escopo restrito do Google, verificação mais pesada, e mistura arquivo que não é do processo.
- **Reusar o token do Gmail:** descartado — o escopo é outro e o consentimento também.
- **Sem seletor (só arquivos que a plataforma criou):** evitaria o token no navegador. Descartado — o advogado já tem os PDFs no Drive.
- **Apagar a pasta no Google ao excluir a pasta da plataforma:** descartado — risco de apagar o que a pessoa organizou lá. A exclusão na plataforma é sempre reversível pelo Google.

## Consequências

- Sem a conta Google conectada, o cofre não lista nem grava arquivos novos. As pastas continuam funcionando.
- A cota consumida é a da conta Google, não a nossa.
- Apagar o arquivo direto no Google tira ele da plataforma na próxima leitura (marcado ausente). O usuário pode tirá-lo da pasta.
- A pasta é livre, então a elaboração sem processo aponta para qualquer pasta escolhida pela pessoa, sem inventar um processo.
- O envio de até 25 MB passa pela memória do backend. Se isso pesar, a saída é o envio resumível direto ao Google.
- Com o app do Google em modo de teste, o refresh token expira em 7 dias. Para clientes reais, publicar o app (o escopo `drive.file` não é sensível, então a verificação é leve).
- Escritório compartilhado (dois advogados na mesma pasta) fica para um Drive compartilhado do Workspace. Não entra neste desenho.
- A peça modelo continua sem ser lida pela IA. Enviar o arquivo ao Drive não faz a IA lê-lo (ADR-016 e ADR-019).

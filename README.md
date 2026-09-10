# Telegram Auto Poster

Sistema simples que monitora fontes autorizadas de vídeos e publica automaticamente no seu grupo privado do Telegram.

Executa periodicamente usando **GitHub Actions** (não precisa deixar nenhum computador ligado). O agendamento de 30 minutos pode sofrer atrasos do GitHub.

---

## O que este projeto faz

1. Verifica fontes configuradas periodicamente
2. Detecta vídeos novos
3. Confere se já foram publicados (evita duplicatas)
4. Baixa o vídeo **somente quando a fonte permite**
5. Envia para o seu grupo do Telegram
6. Registra que já foi publicado
7. Continua monitorando

---

## Requisitos

- Um bot do Telegram (você já tem)
- O bot já adicionado no grupo privado
- Conta no GitHub (você já tem este repositório)

---

## 1. Configurar os Secrets no GitHub (pelo iPhone)

Você precisa criar **dois Secrets**. Nunca coloque o token no código.

### Passo a passo no celular:

1. Abra o repositório no navegador ou app do GitHub:  
   `https://github.com/jufdg-debug/-telegram-auto-poster`

2. Toque em **Settings** (Configurações) do repositório  
   (se não aparecer, toque nos três pontinhos `...` e procure Settings)

3. No menu lateral, toque em **Secrets and variables** → **Actions**

4. Toque em **New repository secret**

### Secret 1 – Token do bot
- **Name**: `TELEGRAM_BOT_TOKEN`
- **Secret**: cole o token completo do seu bot (aquele que o @BotFather te deu)
- Toque em **Add secret**

### Secret 2 – ID do grupo
- **Name**: `TELEGRAM_CHAT_ID`
- **Secret**: `-1003634142944`
- Toque em **Add secret**

Pronto. Os secrets ficam escondidos e o código só os lê em tempo de execução.

---

## 2. (Opcional) Variáveis do repositório

Ainda em **Settings → Secrets and variables → Actions**, vá na aba **Variables**.

Você pode criar:

| Nome                  | Exemplo de valor                          | Para que serve                          |
|-----------------------|-------------------------------------------|-----------------------------------------|
| `DRY_RUN`             | `true` ou `false`                         | Modo teste (não envia de verdade)       |
| `MAX_VIDEOS_PER_RUN`  | `2`                                       | Quantos vídeos por execução             |
| `CAPTION_TEMPLATE`    | `🔥 Novo vídeo\n\n{title}`                | Modelo da legenda                       |

Se não criar, o sistema usa valores padrão seguros.

---

## 3. Como executar um teste manual

1. No repositório, toque em **Actions**
2. No lado esquerdo, toque em **Telegram Auto Poster**
3. Toque em **Run workflow** (botão à direita)
4. Escolha:
   - `dry_run`: **true** (recomendado na primeira vez)
   - `max_videos`: `1` ou `2`
5. Toque em **Run workflow**

Espere alguns segundos e toque na execução que aparecer para ver os logs.

---

## 4. Como ver se funcionou

- Nos logs da execução você verá mensagens como:
  - `[INFO] Iniciando execução`
  - `[INFO] Conteúdo novo encontrado`
  - `[INFO] Publicado com sucesso` (ou `[DRY_RUN] Seria publicado...`)
- Se `DRY_RUN=false` e tudo estiver certo, o vídeo aparece no grupo do Telegram.

---

## 5. Como ativar/desativar o modo teste

- **Pelo workflow manual**: escolha `true` ou `false` no campo dry_run.
- **Permanentemente**: crie a Variable `DRY_RUN` com valor `true` ou `false`.

Quando `DRY_RUN=true` o sistema **detecta e mostra** o que faria, mas **não envia nada** para o Telegram.

---

## 6. Como adicionar novas fontes

As fontes ficam no arquivo `config.py`, na lista `SOURCES`.

Exemplo atual:

```python
SOURCES = [
    {
        "type": "example",
        "name": "Exemplo Seguro (vídeos de teste públicos)",
        "max_items": 2,
    },
]
```

Para uma fonte futura autorizada:

1. Crie um novo arquivo em `sources/` (ex: `minha_fonte.py`)
2. Herde da classe `BaseSource` e implemente `fetch_new_items()`
3. Registre no `sources/__init__.py`
4. Adicione a configuração em `config.py`

O adaptador genérico (`sources/generic_source.py`) está documentado para servir de modelo.

**Importante**: só adicione fontes que você tem autorização para baixar e redistribuir. O sistema não contorna proteções técnicas.

---

## 7. Como alterar a legenda

Crie (ou edite) a Variable do repositório chamada `CAPTION_TEMPLATE`.

Exemplo:

```
🔥 Novo vídeo

{title}
```

O `{title}` é substituído automaticamente pelo título do vídeo.

---

## 8. Estrutura dos arquivos

```
telegram-auto-poster/
├── README.md                 ← este arquivo
├── requirements.txt
├── .gitignore
├── .env.example              ← só para testes locais (não use no celular)
├── config.py                 ← fontes, limites, legenda
├── main.py                   ← lógica principal
├── database.py               ← controle de duplicatas
├── telegram_client.py        ← envio para o Telegram
├── sources/
│   ├── __init__.py
│   ├── base.py               ← classe base
│   ├── generic_source.py     ← modelo para fontes futuras
│   └── example_source.py     ← fonte de teste segura
├── data/
│   └── .gitkeep              ← estado publicado fica aqui
└── .github/workflows/
    └── auto_poster.yml       ← execução automática a cada 30 min
```

---

## 9. Limitações atuais

- Aceita listas de URLs diretas e links de álbuns/perfis do Erome acessíveis sem login.
- Não contorna login, CAPTCHA, DRM, paywall ou bloqueios.
- Tamanho máximo de vídeo configurado em ~45 MB (limite do Telegram Bot é 50 MB).
- A fonte de exemplo usa apenas vídeos públicos de teste (não é Erome nem conteúdo adulto).
- O estado de “já publicado” é salvo no próprio repositório (arquivo `data/published.json`).

---

## 10. Segurança

- O token do bot **nunca** fica no código nem nos logs.
- `.env` e arquivos de banco estão no `.gitignore`.
- Use sempre os **Secrets** do GitHub.

---

## Resumo rápido para começar agora

1. Crie os 2 Secrets (`TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`)
2. Vá em **Actions → Telegram Auto Poster → Run workflow**
3. Coloque `dry_run = true` e rode
4. Veja os logs
5. Se estiver tudo ok, rode de novo com `dry_run = false`

Qualquer dúvida é só perguntar.



## 11. Usar seus álbuns ou perfil do Erome

A fonte `erome` foi adicionada. Ela só é ativada quando `EROME_URLS` está configurado.
O envio continua limitado a 2 vídeos por execução por padrão; o agendamento existente é de 30 minutos.

### Configurar pelo iPhone

1. Abra **Settings → Secrets and variables → Actions → Variables**.
2. Crie ou edite `DRY_RUN` com o valor `true` para começar em modo de teste.
3. Na aba **Secrets**, toque em **New repository secret**.
4. Em **Name**, escreva `EROME_URLS`.
5. Em **Secret**, cole o link do seu álbum (formato `https://www.erome.com/a/ID`) ou do seu perfil (formato `https://www.erome.com/USUARIO`). Pode colocar vários links, um por linha.
6. Salve. O link não deve ser adicionado ao código do repositório.
7. Abra **Actions → Telegram Auto Poster → Run workflow**, selecione `dry_run=true` e execute.
8. Confira se os logs mostram vídeos detectados. O modo de teste verifica a descoberta, sem baixar, publicar ou alterar o histórico.
9. Para testar um envio real, execute manualmente com `dry_run=false` e `max_videos=1`.
10. Depois de confirmar a chegada do vídeo, altere a Variable `DRY_RUN` para `false` para habilitar os envios agendados.

Não é necessário alterar seu token nem o ID do grupo. Para desativar apenas esta fonte, remova o Secret `EROME_URLS`.

### Comportamento e limites

- Álbuns não listados no perfil precisam de seus links diretos em `EROME_URLS`.
- O perfil é consultado com `t=posts`, para pegar os próprios álbuns e excluir repostagens.
- Só extrai arquivos de vídeo dos players dos álbuns; imagens são ignoradas.
- Envia o Referer do álbum no download. Login, desafios de acesso e redirecionamentos de mídia não são contornados.
- IDs de vídeos já enviados são filtrados antes do limite de candidatos, permitindo avançar ao longo das execuções.
- URLs privadas não são impressas nos logs nem gravadas no histórico publicado pelo adaptador.
- O limite existente de 45 MB continua aplicado; arquivos maiores são ignorados, sem compressão automática.
- Por execução, consulta até 10 páginas por perfil e 100 álbuns. As Variables `EROME_MAX_PAGES` e `EROME_MAX_ALBUMS` permitem alterar esses limites.
- Se não houver vídeos detectados, verifique o link e use diretamente o álbum. Mudanças no HTML ou nos servidores de mídia podem exigir atualização do adaptador.
- A integração foi testada com HTML sintético. O acesso ao álbum real e o envio com seus Secrets devem ser verificados no Actions; não foram validados pelo ambiente de desenvolvimento.

### Testes locais

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Os testes simulam as respostas e não acessam vídeos reais nem enviam mensagens.

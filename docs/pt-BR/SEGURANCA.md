[🇺🇸 English (default)](../SEGURANCA.md) · **🇧🇷 Português (Brasil)**

# Segurança e recuperação · DarfinOS

**Seu Arch, minhas regras.** Mas o controle da instalação continua sendo seu.

## Antes de executar

1. Atualize os backups dos seus dados e anote como recuperar o sistema por TTY ou mídia de instalação.
2. Use `python3 DarfinOSInstallScript-TUI.py --doctor` e `--plan --preset minimal` para inspecionar a proposta sem sudo.
3. Execute a TUI como usuário comum, revise seleção e dependências, principalmente pacman, repositórios, shells, SonicDE e XLibre.
4. **Nunca** execute o instalador inteiro como root ou importe repositórios sem avaliar a origem das chaves.
5. Considere `bedrock`, `cleanup`, `firewall`, `repo_cachyos` e a troca de servidor gráfico como etapas avançadas.

## Execução

- `-y` não autoriza toda operação: substituições do pacman e decisões sensíveis ainda exigem interação.
- O preset `full` inclui transformações do sistema: é intencionalmente opt-in.
- O Bash não oferece rollback automático. Uma etapa pode fazer mudanças antes de falhar.
- A TUI mantém eventos, logs e diários de retomada; um hash diferente impede retomada automática na revisão errada.

## Diagnóstico e suporte

```bash
python3 DarfinOSInstallScript-TUI.py --doctor
python3 DarfinOSInstallScript-TUI.py --runs
bash DarfinOSInstallScript.sh --list
```

Logs do Bash: `~/.local/state/postinstall/`; logs da TUI: `~/.local/state/darfinos-tui/logs/`.

Ao abrir uma issue, inclua distribuição, terminal, opções selecionadas e mensagens de erro. **Remova senhas, tokens, IPs privados e demais dados pessoais** dos logs antes de anexar.

[Reportar um problema](https://github.com/AlanDarfin/DarfinOS/issues) · [Voltar ao README](../../README.pt-BR.md)


## Perfis portáteis e backup de configurações (Control Center)

O módulo `darfinos_control.py` não usa sudo e não altera pacotes.
A exportação importa uma seleção de etapas, e **desliga `-y`** ao importar.
Perfis não representam detecção de todos os componentes instalados.

`backup` captura apenas alguns arquivos permitidos em `~/.config`, em ZIP privado
(com modo 0600). Pode incluir senhas ou tokens que o usuário tenha escrito nas
próprias configurações. **Nunca envie o ZIP em issues.**

`restore` sem flags mostra somente uma prévia. Para restaurar é necessário
`--apply` e, se já existir destino, também `--overwrite`.
Antes de substituir um arquivo, a ferramenta guarda o arquivo anterior
com sufixo `.darfinos-pre-restore-*.bak`. A operação de múltiplos arquivos
não é transacional, portanto interrupções podem exigir recuperação manual.

Isso **não** reverte atualizações do pacman, mudanças em serviços, chaves,
XLibre/SonicDE, Bedrock, `/etc` ou operações da TUI.

[Checklist de validação real em VM](VALIDACAO_VM.md) ·
[Preparação do primeiro release](LANCAMENTO.md)

## Seleção explícita no instalador Bash

Para evitar instalar o conjunto inteiro por acidente, iniciar o Bash sem opções
mostra instruções e retorna código 2, **antes de chamar `sudo`**. Selecione
`--only base,cli_tools` ou use a TUI; `--all` inclui Bedrock e outras
opções arriscadas. `--skip` executa todas as etapas restantes, e deve ser
tratado como operação avançada.

Durante uma restauração de configurações, todos os arquivos são preparados
antes de modificar destinos. Falhas de gravação acionam uma tentativa de
reversão dos arquivos previamente alterados, com mensagens em caso de
falhas na reversão. Não existe garantia de transação atômica entre todos os
arquivos ou de proteção contra mudanças simultâneas por outros aplicativos.


Os presets padrão incluem agora um AUR helper quando selecionam manutenção.
Pacotes do AUR são gerenciados por terceiros e podem executar scripts de
compilação/instalação. **Revise as fontes e confirmações** do helper e não
use `-y` como substituto para essa revisão.

## DarfinOS Labs

A categoria [Labs](LABS.md) reúne 13 projetos externos com etapas de
instalação. As etapas avançadas `lab_*` exigem seleção individual, confirmação
`LABS` e não aceitam `-y`. Revise os PKGBUILDs do AUR e teste os
experimentos gráficos e de boot numa VM. Trinity usa um repositório assinado
e não muda o gerenciador de login.

Conty e nix-portable são baixados com verificação de SHA-256. Os experimentos
gráficos não substituem o servidor padrão, e o Booster não troca sua entrada
de boot. Decman e Metapac são instalados sem aplicar regras que possam alterar
pacotes ou arquivos do sistema.

## Chicago95 e detecção de módulos

O verificador `--check-modules` é somente leitura e não chama sudo.
Apenas estados `installed` pulam etapas; estados parciais ou desconhecidos
continuam como pendentes de verificação, sobretudo quando lidam com serviços.
O Chicago95 baixa arquivos do repositório upstream para o usuário, **sem executar**
o instalador `installer.py` e **sem sobrescrever** diretórios já existentes.
A opção `--reinstall` reexecuta etapas, não remove `--needed` do pacman
nem autoriza o overwrite de temas. Veja [MODULOS.md](MODULOS.md).

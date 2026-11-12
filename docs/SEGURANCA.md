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

[Reportar um problema](https://github.com/AlanDarfin/DarfinOS/issues) · [Voltar ao README](../README.md)


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

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

# DarfinOS · Validação de instalação em VM

Este roteiro é uma **matriz manual de aceitação**, não o registro de um teste já executado.
Não executar mudanças de servidor gráfico em máquina pessoal como experimento de CI.

## 1. Preparar ambiente isolado

- [ ] Criar VM descartável com Arch Linux atualizado, rede e acesso ao console/TTY.
- [ ] Criar usuário sem privilégios root com sudo configurado.
- [ ] Registrar versão do Arch, arquitetura, modo de vídeo, snapshot e SHA do commit testado.
- [ ] Criar **snapshot real da VM** antes de instalar; testar como restaurá-lo.
- [ ] Confirmar espaço disponível e acesso à internet. `--preflight` não garante isso.

## 2. Testar inspeção sem alterações

```bash
bash DarfinOSInstallScript.sh --preflight
python3 DarfinOSInstallScript-TUI.py --doctor
python3 DarfinOSInstallScript-TUI.py --plan --preset minimal
python3 DarfinOSInstallScript-TUI.py --status-json
python3 darfinos_control.py status --json
python3 DarfinOSInstallScript-TUI.py --local --dry-run
```

- [ ] O plano Minimal não inclui Bedrock, firewall nem substituição gráfica.
- [ ] A TUI não modifica o sistema enquanto usada somente para inspeção.
- [ ] A tecla C abre a visão de estado do Control Center sem exigir sudo.

## 3. Testar instalação real (somente na VM)

- [ ] Executar primeiro o preset Minimal, revisar transações do pacman e registrar o log.
- [ ] Conferir `pacman -Qi` dos pacotes esperados e distinguir pacotes condicionais.
- [ ] Executar `command -v topgrade arch-update arch-update-tray`.
- [ ] Conferir o autostart do tray **após login gráfico**, avisos, timers e permissões do usuário.
- [ ] Executar um teste **interativo supervisionado** do Topgrade. Não presumir atualização automática.
- [ ] Reexecutar seleção limitada e checar comportamento de etapas já atendidas.
- [ ] Forçar falha não destrutiva controlada para conferir log, estado incompleto e retomada.
- [ ] Confirmar que `--resume` pede revisão e não promete desfazer mudanças.

## 4. Desktop e compatibilidade (snapshot separado)

Restaurar snapshot ou criar nova VM antes das etapas mais arriscadas.

- [ ] Executar pelo console/TTY as etapas para repositórios, XLibre e SonicDE.
- [ ] Confirmar origem de chaves, repositórios, conflitos e prompts do gerenciador.
- [ ] Reiniciar VM e verificar login, sessão X11, áudio, rede, monitor, logout e troca de TTY.
- [ ] Documentar logs e versões efetivas para XLibre, SonicDE, Arch-Update e Topgrade.
- [ ] Restaurar snapshot e verificar que o sistema anterior inicializa.

## 5. Critério para lançamento estável

Somente publicar v0.1.0 após:
- [ ] CI Python/Bash aprovada.
- [ ] Smoke test no contêiner Arch aprovado.
- [ ] Instalação Minimal real aprovada na VM.
- [ ] Desktop + XLibre testados e recuperação via snapshot demonstrada.
- [ ] PR revisado, documentação e links de download conferidos.
- [ ] Pacote e SHA256 publicados com notas indicando riscos conhecidos.

**O Control Center faz backup apenas de certos arquivos do HOME**.
Não cria snapshot, não reverte pacotes e não oferece rollback de pacman/Bedrock/XLibre.


## Verificação complementar (não equivale à VM)

Opcionalmente, após mesclar uma versão revisada dos workflows,
execute manualmente o teste de instalação Base no GitHub Actions em
`.github/workflows/install-base-manual.yml`. Ele modifica somente o
contêiner descartável e não testa inicialização gráfica. Registre o link
exato da execução e o commit SHA antes de considerar o resultado válido.


- [ ] Verificar que o preset Minimal seleciona `aur_helper` antes de `maintenance`.
- [ ] Simular indisponibilidade do AUR: a etapa `maintenance` deve marcar `FAIL`
  quando Topgrade/Arch-Update não forem instalados, sem relatar sucesso falso.

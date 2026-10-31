# Contribuir com o DarfinOS

Obrigado por melhorar este projeto de personalização do Arch Linux.

## Fluxo recomendado

1. Abra uma issue descrevendo o problema e o comportamento esperado.
2. Crie uma branch para a alteração. Evite misturar refatoração, mudanças de temas e alterações destrutivas no mesmo PR.
3. Execute os testes offline:
   ```bash
   bash -n DarfinOSInstallScript.sh
   python3 -m py_compile DarfinOSInstallScript-TUI.py
   python3 -m unittest discover -s tests -v
   python3 DarfinOSInstallScript-TUI.py --doctor
   ```
4. Explique o risco de novas etapas, dependências externas e comportamento com `--only` e `-y`.

## Princípios

- Prefira operações idempotentes e confirmações explícitas para alterações importantes.
- Não inclua `curl | bash` silencioso, segredos ou credenciais no repositório.
- Mantenha o Bash funcional sem a TUI; preserve o contrato `STEPS`, `STEP_DESC`, `STEP_DEPS` e os eventos existentes.
- Testes não devem usar `sudo`, instalar pacotes ou alterar a máquina do contribuinte.

[Guia de segurança](docs/SEGURANCA.md) · [Testes](docs/TESTES.md)

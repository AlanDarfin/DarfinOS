<div align="center">

# ⚡ Testes & Qualidade

**DarfinOS — Seu Arch, minhas regras.**

[← README](../README.md) · [📚 Documentação](./) · [🌐 Site](https://github.com/AlanDarfin/darfinos-website)

</div>

---

Esta camada adiciona testes **sem instalar pacotes**, sem chamar `sudo` e sem precisar de Arch Linux. O instalador de produção permanece independente dos testes.

![GitHub Actions](https://img.shields.io/github/actions/workflow/status/AlanDarfin/DarfinOS/tests.yml?branch=main&label=Testes&style=for-the-badge&labelColor=171717&color=FFCB2E)

> [!NOTE]
> Os testes automatizados validam componentes do projeto, **não** substituem uma instalação de teste em VM nem garantem compatibilidade com todo hardware.

## 🧪 Executar localmente

Requer Python 3.10+ e Bash; `curses` precisa estar disponível na instalação do Python.

```bash
bash -n DarfinOSInstallScript.sh
python3 -m py_compile DarfinOSInstallScript-TUI.py
python3 -m unittest discover -s tests -v
bash DarfinOSInstallScript.sh --list
```

Para rodar a análise opcional, se `shellcheck` estiver instalado:

```bash
shellcheck -S warning DarfinOSInstallScript.sh
```

## O que é testado

- Parser de `STEPS`, `STEP_DESC` e `STEP_DEPS`; ordem e nomes únicos das 32 etapas.
- Dependências, seleção, comando `--only` e proteção contra execução vazia.
- Prévia estática de pacotes, sem instalação.
- Perfis salvos e carregados, validação dos nomes.
- Diário JSON: permissões, transições `PEND/RUN/DONE/FAIL/SKIP`, estado `INCOMPLETE` mesmo com exit code 0.
- Retomada: dependências, etapas já concluídas, estados incertos e proteção SHA-256.
- Funções reais Bash `darfinos_event`, `run_step`, `confirm` e `choose` executadas isoladamente com funções simuladas. O teste **não faz `source` do instalador completo** e nunca alcança o laço real de instalação.
- `--help`, `--runs` e `--list` em subprocessos não interativos.

## GitHub Actions

O workflow `.github/workflows/tests.yml` roda em push para `main`, pull requests e manualmente (`workflow_dispatch`). A matriz usa Python 3.10, 3.12 e 3.13.

O job **validate** bloqueia alterações com falhas de sintaxe ou testes. O job **shellcheck** produz um artifact com os avisos e **não bloqueia**, porque o Bash já tem código legado que pode precisar de revisão gradual. Isso não significa que todos os avisos sejam irrelevantes.

## Limitações

Os testes **não** validam uma instalação real do Arch, pacman/AUR/Flatpak, integração do SonicDE/XLibre/Bedrock, conexão de rede ou fluxo completo de `curses`/PTY em um terminal humano. Esses cenários exigem testes manuais e/ou uma VM descartável. Não use CI como garantia de que o script é seguro para executar em qualquer máquina.

Para alterações futuras: acrescente testes offline sempre que modificar a seleção, o protocolo de eventos ou a lógica de retomada.


## Novas verificações

Os testes verificam o diagnóstico estático de dependências, a presença das funções do Bash, a busca aproximada de etapas e as novas opções CLI `--doctor`, `--doctor-json` e `--plan`.

A auditoria `--doctor` é somente leitura. O Bash agora retorna erro quando termina com etapas falhas ou bloqueadas, facilitando o acompanhamento automatizado.

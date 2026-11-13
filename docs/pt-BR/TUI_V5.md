[🇺🇸 English (default)](../TUI_V5.md) · **🇧🇷 Português (Brasil)**

<div align="center">

# ⚡ Control Center · TUI V5

**DarfinOS — Seu Arch, minhas regras.**

[← README](../../README.pt-BR.md) · [📚 Documentação](../README.md) · [🌐 Site](https://github.com/AlanDarfin/darfinos-website)

</div>

---

A V5 mantém o frontend `curses` em Python padrão e o Bash da V4.4, adicionando uma interface mais organizada sem alterar a lógica do instalador.

## 🖥️ Visão geral

A TUI é a central de controle do instalador. Para ver o projeto em imagens e conhecer a experiência visual, visite a [galeria no site do DarfinOS](https://github.com/AlanDarfin/darfinos-website).

> [!NOTE]
> A interface é baseada em **Python + curses**, não depende de frameworks gráficos e mantém o Bash como responsável pela instalação.

## ✨ O que mudou

- Cabeçalho V5 com fonte, perfil, hash do instalador, estado de `-y` e barra de seleção.
- Lista de etapas com marcadores `■` e `□`, foco destacado e inspeção de descrição longa, grupo, detecção e pacotes previstos por origem. As dependências satisfeitas/ausentes não ocupam espaço: o painel só mostra as pendentes.
- Layout responsivo: inspeção lateral a partir de 100 colunas e resumo abaixo em terminais menores (mínimo 54×16).
- Painel ao vivo com barra de **etapas encerradas**, totais de `DONE`/`FAIL`/`SKIP`, destaque por estado e alternância entre eventos e logs com **L**.
- Atalhos existentes preservados: **O** presets, **Z** retomada, **B** aplicativos, **P** perfis, **M** manutenção, **C** estado do sistema, **V** auditoria dos pacotes, **H** histórico. **T** inicia Topgrade na tela de seleção (após confirmação) e abre terminal integral durante instalação.

## Integração de atualizações

A etapa `maintenance` agora faz parte da instalação padrão sugerida pelos presets. Instala **Topgrade** por `topgrade-bin` e **Arch-Update com seu applet `arch-update-tray`** pelo pacote único `arch-update-bin`, quando existe helper AUR. Tenta habilitar `arch-update --tray --enable` (XDG Autostart) e `arch-update --check --enable` (timer do usuário). Falhas de configuração são mostradas como aviso, por exemplo ao iniciar de um TTY sem serviços de usuário ativos.

A TUI usa **T** na seleção para abrir o Topgrade com os prompts originais do terminal; a atualização não é automática, requer confirmação e é desativada em `--dry-run`. A tecla **U** continua limitada à atualização da fonte do instalador. Na tela de execução, **T** continua significando terminal integral da instalação.

## Limitações

A barra de instalação mede **etapas encerradas**, não pacotes baixados, nem progresso temporal. Uma etapa `FAIL` ou `SKIP` também conta como encerrada, mas **não** como sucesso. As informações de sucesso e falha vêm dos eventos do Bash.

A inspeção e a revisão mostram **uma prévia parcial de pacotes** extraída de chamadas literais no Bash. Condicionais, arrays, pacotes derivados de variáveis e aplicativos escolhidos na execução podem não aparecer. Dependências só ocupam espaço se faltarem etapas no conjunto selecionado.

O frontend não faz rollback e não altera os critérios de retomada da V4.2. A interface curses depende de um terminal interativo; os testes automatizados cobrem lógica pura e execução não interativa, não todos os tamanhos de terminal ou prompts de ferramentas externas.

## Testar

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile DarfinOSInstallScript-TUI.py
bash -n DarfinOSInstallScript.sh
python3 DarfinOSInstallScript-TUI.py --local --dry-run
```

O `--dry-run` não executa a instalação. Para explorar a interface, navegue e saia com **Q** antes de confirmar uma instalação real.


## Atualização de segurança e produtividade

- A seleção inicial usa `minimal` em vez de marcar todas as etapas (inclusive Bedrock).
- Busca de etapas por nome, grupo e descrição, com correspondência aproximada para pequenos erros.
- `--doctor` e `--doctor-json` verificam sintaxe e grafo das etapas sem instalar nada.
- `--plan --preset gaming` imprime um plano estático, também sem sudo nem instalação.
- `--empty` mantém a opção de começar com nenhuma etapa marcada.


## Control Center local

- **C** na seleção: mostra o estado local, ferramentas encontradas, perfis e última execução.
- **V** na seleção: audita pacotes previstos para as etapas marcadas, sem instalar.
- `--audit --preset gaming` ou `--audit --profile NOME`: mostra a auditoria em JSON sem terminal interativo. O inventário é parcial e não identifica conclusão das etapas.
- `python3 DarfinOSInstallScript-TUI.py --status-json`: emite os mesmos dados estruturados sem iniciar a TUI.
- `bash DarfinOSInstallScript.sh --preflight`: checa Arch, pacman, sudo e curl sem solicitar sudo.
- `python3 darfinos_control.py maintenance --json`: detecta Topgrade, Arch-Update, autostart e timers sem atualizar pacotes.
- O Bash exige escolha explícita de etapas (`--only`, `--skip` ou `--all`).
- `darfinos_control.py`: `status`, `profile-export`, `profile-import`,
  `profile-diff`, `backup` e `restore`.

A cópia ZIP inclui apenas arquivos permitidos em `~/.config` (DarfinOS, Fish,
Starship e Fastfetch). Caminhos e checksums são validados. Um restore é apenas
prévia até receber `--apply`; arquivos existentes exigem também `--overwrite`.
O backup **não contém nem restaura configurações em /etc ou pacotes do pacman**.
Pode conter informações privadas: evite compartilhá-lo.

Consulte [VALIDACAO_VM.md](VALIDACAO_VM.md) para a aceitação em VM e
[LANCAMENTO.md](LANCAMENTO.md) para o pacote de versão.


**Mudança de dependência:** os três presets comuns incluem `aur_helper`
antes de `maintenance`, que depende dele. Se Topgrade/Arch-Update não puderem
ser instalados, a etapa reporta falha em vez de declarar sucesso. Isso permite
à TUI marcar corretamente uma instalação incompleta.


### Plano de migração entre presets

`python3 DarfinOSInstallScript-TUI.py --compare-presets minimal gaming`
lista as etapas adicionadas, removidas e que exigem revisão especial para passar
de uma seleção declarativa a outra. **Não** compara os pacotes já instalados
nem habilita remoções automáticas. Execute `--audit` para consultar a prévia
de pacotes locais, sem tomá-la como prova de que uma etapa foi concluída.

## DarfinOS Labs e o novo preset i3

A TUI agora apresenta **64 etapas**, sete presets (minimal, desktop, i3, retro,
workstation, gaming e full) e a tecla **L** para abrir o catálogo de 29 entradas
independentes. O catálogo lê links, modos e riscos diretamente do Bash sem
executar nada. Enter mostra os detalhes e o endereço original; Espaço apenas
marca uma etapa disponível. Use `--labs` ou `--lab-info NOME` sem terminal.

O preset `i3` instala i3 e XLibre com etapas comuns, **sem SonicDE**. Os Labs
AUR (NsCDE, JuNest, Decman e Metapac) são sempre escolhidos um a um, fora do
`full`, do atalho A e de seleções amplas `--all`/`--skip`. A etapa exige
digitar `LABS` e rejeita `-y`; não executa `setup`, `clean` ou perfis
externos automaticamente. Veja [a referência completa](LABS.md).

## Checagem de módulos e reexecução

A tecla **I** usa o mesmo verificador do Bash para classificar cada módulo
como `installed`, `partial`, `missing` ou `unknown`. Somente o primeiro
estado pula uma etapa automaticamente. A tecla **X** reexecuta os módulos
mesmo quando o estado é `installed`; o journal registra `STEP_ALREADY`
como `ALREADY`, sem tratar como falha nem oferecer a etapa na retomada.

A TUI e o Bash expõem `--check-modules` (JSON e TSV, respectivamente), sem sudo.
O preset `retro` combina Xfce e Chicago95, sem alterar automaticamente o tema.
Detalhes: [MODULOS.md](MODULOS.md).

**W** · [Theme Workshop / Oficina de Temas](CUSTOMIZATION.md).

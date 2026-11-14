[🇺🇸 English (default)](../MANIFESTO_PRESETS.md) · **🇧🇷 Português (Brasil)**

<div align="center">

# ⚡ Manifesto & Presets

**DarfinOS — Seu Arch, minhas regras.**

[← README](../../README.pt-BR.md) · [📚 Documentação](../README.md) · [🌐 Site](https://github.com/AlanDarfin/darfinos-website)

</div>

---

O comando `python3 DarfinOSInstallScript-TUI.py --manifest` exporta JSON estático, sem executar o instalador. Use `--list-presets` para listar presets.

## ⚡ Presets em resumo

| Preset | Objetivo | Atenção |
| --- | --- | --- |
| `minimal` | Ferramentas essenciais | Seleção reduzida |
| `desktop` | SonicDE e XLibre | Altera componentes gráficos |
| `i3` | WM i3 + XLibre | Nova sessão X11, sem SonicDE |
| `retro` | Xfce e Chicago95 | Tema opcional no HOME, sem trocar sessão |
| `workstation` | Window Maker e chezmoi | Perfil Workstation 1995 opcional |
| `gaming` | Desktop e jogos | Depende do hardware |
| `full` | Todas as 36 etapas convencionais | Inclui Bedrock e opções avançadas |

> [!IMPORTANT]
> **Preset não é instalação automática.** Confira as etapas selecionadas antes de executar.

## 📦 Contrato

- `schema_version`: versão do formato JSON, atualmente 1.
- `script_sha256`: identifica exatamente o Bash analisado.
- `accuracy: partial_static`: indica cobertura parcial da lista de pacotes.
- `steps[].id`, `description`, `group`, `dependencies`, `packages`: dados por etapa.
- `packages[].manager`: `pacman`, `aur` ou `flatpak`.
- `presets`: seleções declarativas de etapas, não comandos executáveis.

Os dados são extraídos das chamadas literais de wrappers no Bash. **Não interprete a ausência de um pacote como prova de que ele não será instalado.**

## Uso

```bash
python3 DarfinOSInstallScript-TUI.py --manifest > manifest.json
python3 DarfinOSInstallScript-TUI.py --preset minimal --local
python3 -m unittest discover -s tests -v
```

**Full** inclui Bedrock e outras etapas sensíveis. Presets são seleção inicial, não garantia de compatibilidade com todas as máquinas. O script continua pedindo confirmação antes de executar.


## Plano e diagnóstico sem interação

```bash
python3 DarfinOSInstallScript-TUI.py --plan --preset minimal
python3 DarfinOSInstallScript-TUI.py --doctor-json
```

O plano não é um dry-run do pacman: apenas exibe as etapas selecionadas. A TUI inicia com o preset `minimal` selecionado por segurança; `full` exige escolha explícita.


A etapa `maintenance` depende de `aur_helper`. Os presets `minimal`,
`desktop` e `gaming` incluem ambas as etapas para que um sistema novo
possa instalar Topgrade e Arch-Update, sujeitos às perguntas do helper e às
permissões do AUR. Se os executáveis ainda estiverem ausentes no final, a etapa
é considerada incompleta. Isso não equivale a uma instalação já testada em VM.

Na rodada anterior, o manifesto passou a incluir 41 etapas; as cinco etapas novas eram `i3` e
`lab_nscde`, `lab_junest`, `lab_decman`, `lab_metapac`. Os demais projetos
do [catálogo Labs](LABS.md) não são etapas automáticas; seus links e riscos
podem ser consultados com `--labs` ou a tecla L. O `full` contém as 35 etapas
convencionais e exclui todos os `lab_*`.

O sexto preset, `retro`, adiciona `xfce` e `lab_chicago95` com confirmação
e cópia de tema/ícones para o HOME. O catálogo Labs soma 29 entradas e o Bash
65 etapas; o `full` continua excluindo `lab_*`.
Ver [MODULOS.md](MODULOS.md) para a checagem automática de instalações.

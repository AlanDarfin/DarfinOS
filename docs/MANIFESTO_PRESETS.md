<div align="center">

# ⚡ Manifesto & Presets

**DarfinOS — Seu Arch, minhas regras.**

[← README](../README.md) · [📚 Documentação](./) · [🌐 Site](https://github.com/AlanDarfin/darfinos-website)

</div>

---

O comando `python3 DarfinOSInstallScript-TUI.py --manifest` exporta JSON estático, sem executar o instalador. Use `--list-presets` para listar presets.

## ⚡ Presets em resumo

| Preset | Objetivo | Atenção |
| --- | --- | --- |
| `minimal` | Ferramentas essenciais | Seleção reduzida |
| `desktop` | SonicDE e XLibre | Altera componentes gráficos |
| `gaming` | Desktop e jogos | Depende do hardware |
| `full` | Todas as 34 etapas | Inclui Bedrock e opções avançadas |

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

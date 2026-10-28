# Manifesto e presets (V4.4)

O comando `python3 DarfinOSInstallScript-TUI.py --manifest` exporta JSON estático, sem executar o instalador. Use `--list-presets` para listar presets.

## Contrato

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

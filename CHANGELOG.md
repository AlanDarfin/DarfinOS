# Changelog · DarfinOS

O projeto segue desenvolvimento contínuo. Esta lista destaca mudanças verificáveis, sem prometer suporte universal a todas as combinações de Arch/derivados.

## Em preparação — atualização e TUI de novembro de 2026

- Topgrade integrado à TUI: **T** abre o atualizador com confirmação e preserva a interação nativa no terminal.
- **`topgrade-bin`** e **`arch-update-bin`** passam para a etapa `maintenance` em vez de dependerem do pacote opcional de extras.
- `arch-update-bin` entrega Arch-Update e o aplicativo `arch-update-tray` juntos; configuração do XDG Autostart e verificação periódica tentada com avisos claros.
- `maintenance` passa a ser selecionada nos presets básicos, de desktop e jogos.
- Inspeção e revisão da TUI mostram descrições longas, prévia parcial dos pacotes por origem e escondem dependências quando não há pendências.
- Testes offline para a integração e as novas informações da interface.

## Em preparação — auditoria de outubro de 2026

### Segurança e estabilidade
- Seleção inicial da TUI reduzida ao preset `minimal`; o `full` passa a ser escolha explícita.
- Código de saída do Bash não sinaliza mais sucesso se houver etapas falhas ou bloqueadas.
- Ajuste de tema Flatpak deixou de forçar globalmente o Breeze.

### Ferramentas
- Comandos `--doctor`, `--doctor-json` e `--plan` para diagnóstico e planejamento sem modificações.
- Filtro de etapas da TUI reconhece aproximações e pequenos erros de digitação.

### Manutenção
- Documentação sincronizada com as **34 etapas** do instalador.
- Guia de segurança e cobertura adicional de testes.
- Consolidação prevista das verificações de CI.

Histórico anterior: [commits](https://github.com/AlanDarfin/DarfinOS/commits/main) · [releases](https://github.com/AlanDarfin/DarfinOS/releases)

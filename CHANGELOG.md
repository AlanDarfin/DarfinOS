# Changelog · DarfinOS

O projeto segue desenvolvimento contínuo. Esta lista destaca mudanças verificáveis, sem prometer suporte universal a todas as combinações de Arch/derivados.

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

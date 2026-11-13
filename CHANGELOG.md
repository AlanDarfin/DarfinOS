# Changelog · DarfinOS

O projeto segue desenvolvimento contínuo. Esta lista destaca mudanças verificáveis, sem prometer suporte universal a todas as combinações de Arch/derivados.

## Em preparação — detecção de módulos e Chicago95 (novembro de 2026)

- Checagem `--check-modules` no Bash (TSV) e TUI (JSON) antes de instalar,
  distinguindo módulos completos, parciais, ausentes e desconhecidos.
- Omitir apenas módulos comprovadamente completos; evento `STEP_ALREADY`
  e estado `ALREADY` no histórico e retomada.
- `--reinstall` no Bash e tecla X na TUI para reexecutar etapas, preservando
  confirmações e políticas de não sobrescrita.
- Etapa Xfce com pacotes oficiais, Chicago95 opcional com cópia segura dos
  temas/ícones do upstream e novo preset `retro`.
- 41 etapas, seis presets e 13 projetos Labs no catálogo.

## Em preparação — DarfinOS Labs e i3 (novembro de 2026)

- Catálogo de 13 projetos externos, upstream e níveis de risco via `--labs`,
  `--lab-info` e tecla L da TUI.
- Integração do i3 nos repositórios oficiais e novo preset com XLibre.
- Etapas opcionais AUR para NsCDE, JuNest, Decman e Metapac, com confirmação
  especial e sem automatizar execução de seus gerenciadores.
- Guias somente leitura para Conty, nix-portable, Trinity, yserver, xomposite,
  Wayback e Booster. Nenhuma alteração automática de boot ou desktop por esses guias.
- 41 etapas no manifesto e documentação de experimentos/VM.

## Em preparação — Control Center, segurança e release (novembro de 2026)

- O instalador Bash passa a exigir seleção explícita (`--only`, `--skip` ou `--all`): executar sem opções não instala todas as etapas.
- `--preflight` verifica condições básicas sem sudo.
- A etapa `maintenance` depende de `aur_helper`; presets comuns incluem essa dependência. Ausência dos atualizadores essenciais marca a etapa como incompleta.
- Control Center com estado do sistema, auditoria parcial de pacotes, inspeção de Topgrade/Arch-Update e comparação declarativa de presets.
- Perfis exportáveis, importáveis com `yes=false` e comparáveis.
- Backups locais de configurações com SHA256, proteção contra substituição acidental e tentativa de reverter operações interrompidas por erro; **não é rollback de pacotes/sistema**.
- Testes Bash e Python ampliados, smoke em contêiner Arch, workflow manual de instalação Base e pacote candidato com SHA256.
- Checklist de VM e documentação de publicação: release estável bloqueada até validar a instalação real e a recuperação.

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
- Documentação sincronizada com as **41 etapas** do instalador.
- Guia de segurança e cobertura adicional de testes.
- Consolidação prevista das verificações de CI.

Histórico anterior: [commits](https://github.com/AlanDarfin/DarfinOS/commits/main) · [releases](https://github.com/AlanDarfin/DarfinOS/releases)

[🇺🇸 English (default)](../LABS.md) · **🇧🇷 Português (Brasil)**

# DarfinOS Labs · projetos independentes e experimentais

**Seu Arch, minhas regras.** Os 13 projetos independentes agora têm uma etapa no instalador. Na TUI, pressione **L** para abrir o Labs, **Enter** para ler os detalhes e **Espaço** para selecionar. No Bash, passe o nome da etapa para `--only`.

```bash
bash DarfinOSInstallScript.sh --labs
bash DarfinOSInstallScript.sh --lab-info trinity
bash DarfinOSInstallScript.sh --only lab_trinity
```

As etapas `lab_*` são interativas, recusam `-y` e ficam fora de `--all`, `--skip` e do preset `full`. O preset Retro inclui Chicago95, e o i3 também existe como etapa convencional. O instalador pula etapas que consegue verificar como completas. Para o AUR, pode preparar yay ou paru quando necessário e pede que você revise o PKGBUILD.

| Projeto | Etapa | O que instala |
| --- | --- | --- |
| [i3](https://i3wm.org/) | `i3` | Pacotes oficiais do Arch para uma sessão X11 paralela. |
| [Chicago95](https://github.com/grassmunk/Chicago95) | `lab_chicago95` | Xfce, temas GTK/XFWM, ícones, cursores e fontes VGA. Preserva os arquivos existentes. |
| [NsCDE](https://github.com/NsCDE/NsCDE) | `lab_nscde` | `nscde` pelo AUR. Escolha NsCDE na tela de login para iniciar a configuração. |
| [JuNest](https://github.com/fsquillace/junest) | `lab_junest` | `junest-git` e um ambiente Arch no HOME com `junest setup`. Não altera os namespaces do sistema. |
| [Decman](https://github.com/kiviktnm/decman) | `lab_decman` | `decman` pelo AUR, sem aplicar perfil Python ao sistema. |
| [Metapac](https://github.com/ripytide/metapac) | `lab_metapac` | `metapac` pelo AUR, sem rodar `sync` ou `clean`. |
| [Conty](https://github.com/Kron4ek/Conty) | `lab_conty` | Conty Lite 1.29.4 (x86_64), verificado por SHA-256, e FUSE. Depois rode `~/.local/bin/conty <comando>`. |
| [nix-portable](https://github.com/DavHau/nix-portable) | `lab_nix_portable` | Binário v012 x86_64 verificado em `~/.local/bin`, sem daemon. Rode `~/.local/bin/nix-portable nix --version` para inicializar o cache. |
| [Trinity](https://www.trinitydesktop.org/) | `lab_trinity` | Repositório assinado do Trinity e desktop completo `tde-meta`, com `pacman -Syu`. |
| [yserver](https://github.com/joske/yserver) | `lab_yserver` | `yserver` e `starty` pelo AUR, com opção de instalar Vulkan Intel ou AMD. Para outras GPUs, use o driver correspondente. |
| [Xomposite](https://github.com/demostenex/xomposite) | `lab_xomposite` | Dependências do Arch e compilação de uma revisão fixa em `~/.local/bin/xomposite`. Use numa sessão X11 sem outro compositor. |
| [Wayback](https://gitlab.freedesktop.org/wayback/wayback) | `lab_wayback` | `wayback-x11` pelo AUR, sem substituir o servidor gráfico padrão. |
| [Booster](https://github.com/anatol/booster) | `lab_booster` | Pacote oficial cujo hook gera imagens initramfs alternativas. O DarfinOS não troca a entrada de boot. |

### Depois de instalar

- **Trinity:** o instalador confere a impressão digital completa publicada e faz backup antes de gravar uma nova seção `[trinity]`. O gerenciador de login é mantido. Escolha Trinity na tela de login X11. [Instruções originais para Arch](https://wiki.trinitydesktop.org/Arch_Trinity_Repository_Installation_Instructions).
- **Chicago95:** selecione o tema, os ícones e os cursores no Xfce. Configurações opcionais de GTK4, painel, sons de login e greeters não são aplicadas. [Guia original do Chicago95](https://github.com/grassmunk/Chicago95/blob/master/INSTALL.md).
- **Gráficos e boot:** teste `starty` em um TTY livre depois de conferir Vulkan e acesso aos dispositivos. Teste Wayback em uma sessão separada. Na VM, experimente Booster com uma entrada de boot alternativa, mantendo a original. [Guia do yserver](https://github.com/joske/yserver/blob/master/docs/setup.md) · [Booster na ArchWiki](https://wiki.archlinux.org/title/Booster).
- **Portáteis e declarativos:** a instalação não altera os namespaces do sistema, não aplica seu inventário de pacotes e não garante isolamento total. Você escolhe o que executar e sincronizar.

[Índice da documentação](README.md) · [Checagem de módulos](MODULOS.md) · [Labs no site](https://darfinos.vercel.app/pt-br/labs/)

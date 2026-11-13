# Depois da instalação · Oficina de Temas
[English](../CUSTOMIZATION.md)

Na TUI, **L** instala as ferramentas do Labs e **W** abre a Oficina.
Presets escolhem pacotes. Perfis de personalização mudam arquivos escolhidos
no HOME, com prévia, aplicação seletiva e histórico para desfazer. O desfazer
preserva arquivos editados após a aplicação. Em `--dry-run`, **W** só consulta.

```bash
bash DarfinOSInstallScript.sh --only lab_chezmoi,lab_matugen,lab_kvantum
python3 darfinos_control.py styles
python3 darfinos_control.py style sonicde-kvantum
python3 darfinos_control.py palette ~/wallpaper.png
python3 darfinos_control.py style-history
python3 darfinos_control.py style-undo IDENTIFICADOR
```

- **Terminal**, **i3 Compacto** e **Workstation 1995** usam templates locais do chezmoi sem importar seu repositório pessoal. No Window Maker, aplique o perfil e depois selecione DarfinOS-1995 no menu de estilos.
- **SonicDE + Kvantum** cria DarfinOSGold com base no tema SVG KvDark. Aplique os quatro arquivos juntos e reabra os aplicativos Qt ou a sessão. Se a sessão sobrescrever a preferência, selecione Kvantum em Estilo dos aplicativos e DarfinOSGold no Kvantum Manager. Painel, KWin e tela de login ficam como estão.
- **Xfce**. Com Chicago95 e os utilitários de desktop instalados, use **W → X** dentro do Xfce. Só muda tema, ícones, cursor e estilo do Xfwm. Esse ajuste ao vivo via Xfconf fica fora do histórico de arquivos dos perfis.
- **autorandr**. Depois de ajustar a tela, salve com `autorandr --save notebook-720p` e teste `autorandr --change`. Só grave 30 Hz se esse modo já funcionar no painel.
- **Manutenção**. `python3 darfinos_control.py maintenance --json` lista pendências com `pacdiff --output`. De uma cópia permanente, rode `python3 darfinos_control.py maintenance-timer enable` para receber avisos semanais, sem atualizar nada. Para desligar, use `maintenance-timer disable`.
- **Backups**. O etckeeper oferece histórico local do /etc. O rustic não cria destino, senha ou agendamento sozinho. Nenhum dos dois substitui um snapshot do sistema.

Veja as novas etapas e os links originais no [DarfinOS Labs](LABS.md). Arcan/Pipeworld e as sessões gráficas ainda precisam de validação em VM.

## i3 Notebook (720p)

O perfil **i3 Notebook** é separado do i3 Compacto. Instale **i3 Notebook** pelo
Labs (**L**), abra **W → i3-notebook**, revise a prévia e aplique. Ele guarda a
configuração anterior do i3 no histórico da Oficina e não sobrescreve suas
configurações globais de Rofi ou Dunst. Encerre e entre novamente na sessão i3
para carregar os utilitários do perfil. Não precisa instalar XLibre se já tem
um servidor X11 funcionando.

```bash
bash DarfinOSInstallScript.sh --only lab_i3_notebook
python3 darfinos_control.py style i3-notebook
python3 darfinos_control.py style i3-notebook --apply --all-files
```

| Atalho | Ação |
| --- | --- |
| Super+D / Super+Tab | Apps e janelas no Rofi. dmenu fica de reserva para apps. |
| Super+F1 | Lista de atalhos, disponível também como aba **Atalhos do i3** no Rofi. |
| Super+B | Modo Escrita. A barra some e volta enquanto você segura Super ou se houver uma janela urgente. |
| Super+Grave / Super+R | Terminal de bolso e redimensionamento com as setas (Esc para sair). |
| Teclas de brilho e áudio | Brilho, volume e mute. O perfil usa o PipeWire ou PulseAudio já configurado. |
| Super+L / Print | Bloquear tela ou capturar uma área. A sessão também usa xss-lock antes de suspender. |
| Super+N / Super+Shift+N / Super+Ctrl+N | Recuperar a última notificação, ativar ou desativar o Não Perturbe e dispensar os pop-ups. |

A barra mostra bateria, rede, volume e hora. O Dunst exibe até três notificações
no canto superior direito, com fundo grafite e a cor de destaque do Rofi.
Se outro daemon de notificações já estiver ativo no mesmo barramento D-Bus, o
perfil não o encerra. Nesse caso, saia do outro ambiente e entre na sessão i3
para testar. Dentro do i3, rode `dunstify "DarfinOS" "Notificações prontas"` para
ver o tema. A personalização não instala nem inicia o Picom.

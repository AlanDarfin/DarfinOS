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

![i3 Notebook em uma sessão X11 isolada de 1280×720](../assets/i3-notebook-720p.png)

O perfil **i3 Notebook** é separado do i3 Compacto. Instale **i3 Notebook** pelo
Labs (**L**), abra **W → i3-notebook**, revise a prévia e aplique. Ele guarda a
configuração anterior do i3 no histórico da Oficina e não sobrescreve suas
configurações globais de Polybar, Rofi ou Dunst. Encerre e entre novamente na sessão i3
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
| Super+F2 | Mostra a resolução e os Hz atuais por saída. Se a tela interna oferecer 1280×720, dá para testar o modo sem escala. Sem confirmar em 15 s, restaura modo, Hz e transformação anteriores. |
| Super+Shift+P | Escolhe uma imagem e reaplica ao entrar no i3, ou restaura o fundo DarfinOS. Também disponível em **Fundo**, na barra. |
| Super+Enter / Super+B / Super+E | Abre o terminal, o navegador padrão ou a pasta pessoal no gerenciador de arquivos padrão. |
| Super+Shift+B | Mostra ou oculta a barra para liberar espaço na tela. |
| Super+1–9 / Super+0 | Vai para as áreas 1–10. Com Shift, move a janela atual. |
| Super+Ctrl+Tab | Volta à área anterior. |
| Super+H / Super+V / Super+Ctrl+E | Divide na horizontal ou vertical, ou alterna a direção da divisão atual. |
| Super+W / Super+S | Organiza as janelas em abas ou em pilha. |
| Super+Shift+Enter ou Super+Grave / Super+R | Terminal de bolso e redimensionamento com as setas (Esc para sair). |
| Teclas de brilho e áudio | Brilho, volume e mute. O perfil usa o PipeWire ou PulseAudio já configurado. |
| Print / Super+Shift+S / Shift+Print | Os dois primeiros selecionam uma área. Shift+Print copia a tela inteira. |
| Super+L | Bloqueia a tela. A sessão também usa xss-lock antes de suspender. |
| Super+N / Super+Shift+N / Super+Ctrl+N | Recuperar a última notificação, ativar ou desativar o Não Perturbe e dispensar os pop-ups. |

A Polybar de 28 px fica no topo, com divisões em seta, tipografia JetBrains Mono
e título curto da janela ativa. **Apps**, **Janelas**, **Atalhos** e **Fundo** são
clicáveis. Brilho, bateria, rede, volume e hora aparecem à direita conforme o
hardware disponível. A primeira área é **1**. **Super+Enter** abre o terminal.
As janelas recebem foco ao passar o mouse, sem mover o ponteiro ao trocar de
monitor pelo teclado. Se a Polybar estiver ausente ou falhar ao iniciar, a barra
nativa do i3 fica como reserva.

O desktop combina superfícies grafite com blocos de status dourados, bronze e
areia. A área de trabalho focada recebe um fundo na cor de destaque; janelas
inativas usam bordas discretas. O launcher centralizado tem busca em uma
superfície própria e linhas mais espaçosas. O fundo traz diagonais sutis, a
marca DarfinOS e o lema do sistema.

O visual da barra e do Rofi foi inspirado nos [dotfiles do iamabhas](https://github.com/iamabhas/dotfiles),
com as cores e os atalhos do DarfinOS. A cor de destaque escolhida na Oficina
é aplicada na barra, no Rofi, no Dunst e no papel de parede padrão.

A etapa Notebook dos Labs instala o [Bibata Modern Ice](https://github.com/ful1e5/Bibata_Cursor)
v2.0.7 da release oficial, com SHA-256 fixo, em
`${XDG_DATA_HOME:-~/.local/share}/icons`. Instalações existentes são preservadas.
O perfil reaproveita o tema e o tamanho do cursor configurados no SonicDE, quando
o tema está instalado. Se não achar o tema escolhido, usa uma variante Bibata
instalada (24 px por padrão). A sessão i3 não altera os arquivos do SonicDE.
Recarregar o perfil atualiza o provedor XSETTINGS que ele próprio iniciou,
preservando provedores de outros ambientes.

A opção de 720p só mexe na tela interna, não inventa modos nem força taxa de
atualização. Se o painel não oferecer 1280×720, o menu explica a indisponibilidade.
A escolha confirmada é reaplicada ao entrar com escala 1:1; **Super+F2 → Parar de
reaplicar 720p ao entrar** desativa essa preferência. Monitores externos mantêm
suas configurações. Sem imagem selecionada, o perfil usa o fundo grafite com o
duplo raio e o lema do DarfinOS. **Fundo → Restaurar fundo DarfinOS** remove a
preferência de imagem personalizada. Se uma imagem salva sumir, o fundo padrão
é usado temporariamente. Se estiver atualizando o perfil, rode o Labs novamente
para instalar as novas dependências antes de reaplicar pela Oficina.

O Dunst exibe até três notificações no canto superior direito, abaixo da barra,
com fundo grafite e a cor de destaque do Rofi.
Se outro daemon de notificações já estiver ativo no mesmo barramento D-Bus, o
perfil não o encerra. Nesse caso, saia do outro ambiente e entre na sessão i3
para testar. Dentro do i3, rode `dunstify "DarfinOS" "Notificações prontas"` para
ver o tema. A personalização não instala nem inicia o Picom.

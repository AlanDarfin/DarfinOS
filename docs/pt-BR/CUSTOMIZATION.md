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

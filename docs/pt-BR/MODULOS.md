[🇺🇸 English (default)](../MODULOS.md) · **🇧🇷 Português (Brasil)**

# Verificação de módulos instalados · DarfinOS

O instalador agora consulta o estado do Arch **antes de executar cada etapa**,
usando os pacotes registrados pelo pacman e, no caso do Chicago95, os arquivos
da pasta do usuário. Não chama `sudo`, não instala nada e não precisa de rede.

## Como verificar

```bash
# Modo legível por script (TSV), sem root
bash DarfinOSInstallScript.sh --check-modules

# Estado estruturado na TUI (JSON)
python3 DarfinOSInstallScript-TUI.py --check-modules

# Abrir TUI: I atualiza checagem; X força reexecutar etapas
python3 DarfinOSInstallScript-TUI.py --local

# Instalar apenas o que for necessário (consultando antes de cada etapa)
bash DarfinOSInstallScript.sh --only base,xfce,lab_chicago95

# Reexecutar etapas marcadas mesmo quando o módulo parecer completo
bash DarfinOSInstallScript.sh --only xfce --reinstall
```

O `--reinstall` desativa a **omissão da etapa**. Ele não remove `--needed` do
pacman, não sobrescreve arquivos Chicago95 existentes e não desativa confirmações.
Seu propósito é corrigir a configuração ou executar novamente a etapa, não forçar
uma substituição de pacotes.

## Estados da checagem

| Estado | Significado | O instalador pula? |
| --- | --- | --- |
| `installed` | Verificação suficiente dos pacotes ou arquivos do módulo específico | **Sim**, registra `STEP_ALREADY` |
| `partial` | Há indícios de instalação, mas faltam componentes ou configurações | Não |
| `missing` | Principais pacotes/arquivos esperados não foram encontrados | Não |
| `unknown` | Não é possível provar conclusão só por uma checagem local | Não |

**A checagem é propositalmente conservadora.** Uma instalação de `sonicde-meta`
não garante que SDDM/SonicLogin, PipeWire e NetworkManager estejam configurados,
por exemplo. O estado permanece parcial. Da mesma forma, detectar pacotes
do Docker, Bluetooth ou Topgrade **não prova** que os serviços ou timers estejam
corretos. Etapas de repositórios, boot, atualizações, firewall e configurações
dinâmicas nunca são ignoradas sem evidências suficientes.

Módulos atualmente com prova de conclusão automática:

- Pacotes **Base** (conjunto literal essencial da etapa).
- **i3** e **Xfce** (todos os pacotes previstos na etapa).
- **AUR helper** (yay ou paru presente no PATH).
- **NsCDE**, **JuNest**, **Decman**, **Metapac** (pacote instalado, sem prometer configuração adicional).
- **Trinity e JuNest** (pacotes e, respectivamente, repositório/sessão e ambiente local).
- **Chicago95** (temas, ícones, cursores e fontes presentes no HOME, com Xfce instalado).

A lista evolui conforme criamos testes e validações específicas para cada módulo.
O comando `--audit` continua sendo uma prévia de pacotes, não um substituto para
a verificação da etapa inteira.

## Execução e histórico

Ao encontrar um módulo `installed`, o Bash informa que ele foi detectado e
emite o evento `STEP_ALREADY`. A TUI registra o estado `ALREADY` no painel
e no histórico; a retomada não oferece essas etapas como pendentes.
Módulos parciais ou desconhecidos **não** ganham esse estado artificialmente.

A verificação não prova que versões estão atualizadas, que o programa inicia
ou que sua configuração segue as preferências mais recentes. Por isso o
`--reinstall` existe e as atualizações de sistema continuam sendo explícitas.

## Xfce + Chicago95

```bash
python3 DarfinOSInstallScript-TUI.py --plan --preset retro
bash DarfinOSInstallScript.sh --only xfce,lab_chicago95
```

O preset `retro` seleciona `base`, `xfce` e `lab_chicago95`. O Xfce usa
pacotes oficiais do Arch, sem substituir SonicDE ou o login manager.
O Chicago95 busca uma revisão fixa do repositório original, valida os links internos e copia temas, ícones, cursores e fontes para o HOME.

O instalador **não executa `installer.py`** do upstream, não aplica temas
GTK4, fontes, cursores, painéis ou configurações do Xfce automaticamente e
recusa sobrescrever pastas existentes. Para habilitar o visual, abra
*Xfce → Aparência* e escolha Chicago95 (Estilo e Ícones), e depois
*Gerenciador de Janelas → Chicago95*. Leia a
[documentação original](https://github.com/grassmunk/Chicago95/blob/master/INSTALL.md)
para aprimoramentos como a barra e o menu clássico.

**Atenção:** o Chicago95 pode alterar a experiência visual de aplicativos GTK
que compartilharem o mesmo usuário se você aplicar o tema globalmente.
Esse controle permanece manual. O projeto não é afiliado à Microsoft ou ao
Chicago95 original.

Voltar ao [README](../../README.pt-BR.md) · [Catálogo Labs](LABS.md) ·
[Checklist de VM](VALIDACAO_VM.md) ·
[Website](https://darfinos.vercel.app/controle/).

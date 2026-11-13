# Documentação do DarfinOS

**[🇺🇸 English (default)](../README.md) · 🇧🇷 Português (Brasil)**

O DarfinOS é um projeto de personalização e pós-instalação do Arch Linux com **41 etapas**, **seis presets** e um catálogo de **13 projetos Labs**. Não é uma distribuição com ISO própria.

Leia o [README completo em português](../../README.pt-BR.md) e os guias:

- [TUI e Control Center](TUI_V5.md), navegação, instalação e acompanhamento.
- [Checagem de módulos](MODULOS.md) e opção de reinstalação.
- [Manifesto e presets](MANIFESTO_PRESETS.md).
- [DarfinOS Labs](LABS.md), com links originais e riscos.
- [Segurança e recuperação](SEGURANCA.md).
- [Validação em máquina virtual](VALIDACAO_VM.md).
- [Testes e qualidade](TESTES.md).
- [Lançamentos e candidatos](LANCAMENTO.md).

## Antes de instalar

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS
python3 DarfinOSInstallScript-TUI.py --doctor
python3 DarfinOSInstallScript-TUI.py --check-modules
python3 DarfinOSInstallScript-TUI.py --local
```

Os diagnósticos são somente leitura. A TUI não inicia instalações ao abrir.

## Downloads

[Baixar ZIP atual da main](https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip) ·
[Ver pré-lançamentos no GitHub](https://github.com/AlanDarfin/DarfinOS/releases) ·
[Página de downloads em português](https://darfinos.vercel.app/pt-br/downloads/).

**Atenção:** candidatos de desenvolvimento não são releases estáveis; ainda faltam testes gráficos e de recuperação em VM.

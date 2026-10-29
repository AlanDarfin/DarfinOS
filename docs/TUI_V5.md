<div align="center">

# ⚡ Control Center · TUI V5

**DarfinOS — Seu Arch, minhas regras.**

[← README](../README.md) · [📚 Documentação](./) · [🌐 Site](https://github.com/AlanDarfin/darfinos-website)

</div>

---

A V5 mantém o frontend `curses` em Python padrão e o Bash da V4.4, adicionando uma interface mais organizada sem alterar a lógica do instalador.

## 🖥️ Visão geral

A TUI é a central de controle do instalador. Para ver o projeto em imagens e conhecer a experiência visual, visite a [galeria no site do DarfinOS](https://github.com/AlanDarfin/darfinos-website).

> [!NOTE]
> A interface é baseada em **Python + curses**, não depende de frameworks gráficos e mantém o Bash como responsável pela instalação.

## ✨ O que mudou

- Cabeçalho V5 com fonte, perfil, hash do instalador, estado de `-y` e barra de seleção.
- Lista de etapas com marcadores `■` e `□`, foco destacado e inspeção de descrição, grupo, dependências e detecção.
- Layout responsivo: inspeção lateral a partir de 100 colunas e resumo abaixo em terminais menores (mínimo 54×16).
- Painel ao vivo com barra de **etapas encerradas**, totais de `DONE`/`FAIL`/`SKIP`, destaque por estado e alternância entre eventos e logs com **L**.
- Atalhos existentes preservados: **O** presets, **Z** retomada, **B** aplicativos, **P** perfis, **M** manutenção, **H** histórico, **T** terminal integral durante instalação.

## Limitações

A barra de instalação mede **etapas encerradas**, não pacotes baixados, nem progresso temporal. Uma etapa `FAIL` ou `SKIP` também conta como encerrada, mas **não** como sucesso. As informações de sucesso e falha vêm dos eventos do Bash.

O frontend não faz rollback e não altera os critérios de retomada da V4.2. A interface curses depende de um terminal interativo; os testes automatizados cobrem lógica pura e execução não interativa, não todos os tamanhos de terminal ou prompts de ferramentas externas.

## Testar

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile DarfinOSInstallScript-TUI.py
bash -n DarfinOSInstallScript.sh
python3 DarfinOSInstallScript-TUI.py --local --dry-run
```

O `--dry-run` não executa a instalação. Para explorar a interface, navegue e saia com **Q** antes de confirmar uma instalação real.

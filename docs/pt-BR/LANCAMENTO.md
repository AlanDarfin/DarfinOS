[🇺🇸 English (default)](../LANCAMENTO.md) · **🇧🇷 Português (Brasil)**

# Downloads e pré-lançamentos do DarfinOS

O DarfinOS **não é uma distribuição ISO**. Antes, a página de releases do GitHub estava vazia porque a automação criava apenas artifacts temporários do Actions, que não são releases publicadas.

## Onde baixar

- **[ZIP da branch main](https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip)**: está sempre disponível, mas corresponde ao código em desenvolvimento, **não a uma versão estável**.
- **[Pré-lançamentos no GitHub](https://github.com/AlanDarfin/DarfinOS/releases)**: arquivos `darfinos-0.1.0-rcN.tar.gz` e seus `sha256`, quando publicados.
- **[Página bilíngue de downloads](https://darfinos.vercel.app/pt-br/downloads/)**: apresenta imediatamente o ZIP da main e detecta candidatos publicados pela API pública do GitHub. Se não houver candidato, exibe uma mensagem em vez de apontar silenciosamente para uma página vazia.

## Nova automação de release

O workflow `.github/workflows/publish-development.yml` é ativado depois que o smoke no contêiner Arch termina com sucesso em um push na `main`. Antes de publicar, ele exige a aprovação **dos testes Python/Bash para o mesmo SHA** e verifica novamente a sintaxe, o Doctor e o pacote/arquivo de checksum.

A publicação usa `gh release create` com `--prerelease`, **nunca como versão estável**. O pacote contém arquivos versionados gerados com `git archive HEAD`. A versão de candidato segue `v0.1.0-rcN`. Se o Actions não tiver permissão para criar a release, o usuário poderá consultar o log; o ZIP de código continua disponível.

O workflow manual `release-candidate.yml` continua produzindo apenas artifact de CI para revisão, com validade limitada, sem publicar release.

## Estabilidade

Um lançamento estável depende da [validação manual na VM](VALIDACAO_VM.md), incluindo login gráfico, reinicialização, sessões XLibre/SonicDE e recuperação de mudanças críticas. A CI automatizada por si só não substitui essa validação.

[Voltar à documentação em português](README.md) · [Guia de segurança](SEGURANCA.md)

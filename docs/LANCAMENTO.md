# Primeiro lançamento do DarfinOS

**Estado: preparação de candidato. Nenhuma versão estável é declarada neste arquivo.**

## Pacote

```bash
bash -n DarfinOSInstallScript.sh
python3 -m unittest discover -s tests -v
python3 DarfinOSInstallScript-TUI.py --doctor
bash scripts/package_release.sh 0.1.0-rc1
sha256sum -c dist/darfinos-0.1.0-rc1.tar.gz.sha256
```

O script usa `git archive HEAD`, empacota os arquivos rastreados e gera SHA256.
Em GitHub Actions, o workflow **DarfinOS · Preparar pacote candidato** pode
ser executado manualmente; ele anexa um artifact temporário, **não publica release**.

## Publicação estável

1. Concluir a lista de aceitação em [VALIDACAO_VM.md](VALIDACAO_VM.md).
2. Revisar as alterações na branch e mesclar PR após CI verde.
3. Criar tag semântica sobre um commit **testado** da main.
4. Gerar o pacote da tag, conferir o SHA256 e publicar ambos no GitHub Releases.
5. Documentar incompatibilidades, origem de repositórios e instruções de recuperação.
6. Depois de publicado, apontar o site para a versão real, mantendo o ZIP da main
   claramente descrito como **código em desenvolvimento**.

Nunca chamar o ZIP da main de release estável. Evitar URLs para `releases/latest`
enquanto não houver uma versão verificada. Não há ISO no projeto.


O teste manual `install-base-manual.yml` pode comprovar a instalação real
de pacotes da etapa Base em contêiner Arch, mas não substitui a validação
em VM do ambiente gráfico e seus procedimentos de recuperação.

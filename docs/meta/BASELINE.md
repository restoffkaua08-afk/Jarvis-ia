# Baseline protegido da evolução Jarvis

## Identificação

- Repositório: `restoffkaua08-afk/Jarvis-ia`
- Upstream: `open-jarvis/OpenJarvis`
- Branch de evolução: `evolution/jarvis-meta-zane`
- Commit-base imutável: `759bfd0b98e9f0d391aa8482ca7b3c7dbd5bceea`
- Licença herdada: Apache-2.0
- Data do registro: 2026-08-24

## Evidências validadas no Windows

- Python 3.13.15 funcional.
- Ambiente virtual criado com uv.
- Dependências do perfil desktop instaladas.
- Importação de `openjarvis` validada.
- CLI `jarvis --help` validada.
- Frontend instalado e compilado.
- Interface web executada em `http://127.0.0.1:8000`.
- Ollama 0.32.15 e `qwen3.5:2b` executados.
- Árvore de trabalho limpa após restaurar artefato incremental do TypeScript.
- Extensão Rust/Tauri nativa ainda não validada por falha externa de conexão durante o download do toolchain.

## Problemas observados no uso

1. Resposta factual incorreta com modelo de 2 bilhões de parâmetros.
2. Latência elevada até para tarefas simples.
3. Seleção do modo multiagente em tarefas que não a justificavam.
4. Resposta de código interrompida.
5. Erro de rede sem recuperação adequada.
6. Encerramento por limite máximo de turnos sem resposta final.
7. Crescimento excessivo do contexto.
8. Ausência de orientação em português na interface.
9. Dependências do frontend com alertas que exigem auditoria controlada.

## Regra de proteção

A branch `main` representa o baseline importado. Toda evolução Meta/Zane ocorre em branch própria, com alterações pequenas, testáveis e reversíveis. Nenhuma mudança deve ser incorporada à `main` sem evidência de testes e revisão dos impactos de segurança, compatibilidade e dados.

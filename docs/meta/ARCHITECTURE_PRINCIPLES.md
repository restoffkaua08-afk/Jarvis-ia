# Princípios de arquitetura Jarvis, Rachel e Zane

## Papel do Jarvis

O Jarvis continuará sendo um produto autônomo, instalável e utilizável sem Rachel ou Zane. A evolução pode utilizar infraestrutura local, GPU dedicada, servidor, cluster ou provedores externos. O computador de desenvolvimento não define o teto arquitetural do produto.

## Compatibilidade sem acoplamento

Jarvis e Rachel não compartilharão bancos internos, estado mutável ou módulos privados diretamente. A interoperabilidade será oferecida por contratos públicos e versionados:

- APIs e eventos com schemas explícitos;
- adaptadores substituíveis;
- identificadores, timestamps e erros normalizados;
- autenticação e autorização por capacidade;
- idempotência para comandos com efeitos;
- negociação de versão e funcionalidades;
- exportação e importação portáveis;
- rastreamento distribuído sem exposição de segredos.

## Destino Zane

Zane não será uma execução permanente de “Jarvis + Rachel”. O objetivo é consolidar configurações e capacidades validadas em uma arquitetura própria. Tecnologias herdadas devem continuar substituíveis.

## Fronteiras mínimas

1. **Model Runtime:** modelos, providers, roteamento, streaming e geração.
2. **Agent Runtime:** planejamento, turnos, delegação, orçamento e recuperação.
3. **Tool Runtime:** catálogo, MCP, execução, sandbox e aprovações.
4. **Memory Runtime:** fatos, conversas, documentos, embeddings e retenção.
5. **Policy Runtime:** identidade, permissões, risco e auditoria.
6. **Experience Layer:** web, desktop, voz, acessibilidade e localização.
7. **Observability:** logs, métricas, traces, custos e avaliações.
8. **Compatibility Layer:** contratos para Rachel e futura consolidação no Zane.

## Perfis de execução

- Desenvolvimento mínimo: validações rápidas sem prometer qualidade de produção.
- Local CPU: operação funcional com degradação explícita.
- Local GPU: modelos maiores e ferramentas aceleradas.
- Servidor GPU: vLLM ou runtime equivalente, concorrência e filas.
- Híbrido: local por privacidade e cloud por capacidade, conforme política.
- Cluster: múltiplos modelos, workers, filas e alta disponibilidade.

A escolha de perfil altera capacidade e desempenho, não a semântica dos contratos.

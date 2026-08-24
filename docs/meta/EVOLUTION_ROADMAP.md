# Roteiro de evolução orientado por evidências

## Gate J0 — Proteção e inventário

- [x] Fixar commit-base.
- [x] Criar branch de evolução isolada.
- [x] Registrar ambiente e evidências já validadas.
- [ ] Mapear componentes, fluxos de dados e superfícies de ataque.
- [ ] Inventariar testes, dependências, configurações e migrations.
- [ ] Criar matriz de funcionalidades da CLI e da interface.

## Gate J1 — Segurança e confiabilidade

- Política deny-by-default para ferramentas perigosas.
- Autorizações por capacidade, escopo, recurso e duração.
- Aprovação humana configurável para efeitos externos.
- Sandbox para shell, arquivos, navegador e código.
- Proteção de credenciais e redação de logs.
- Idempotência, deduplicação, timeout e cancelamento.
- Persistência atômica e recuperação de configurações.
- Scheduler com timezone explícito.
- Servidor local seguro por padrão.

## Gate J2 — Inteligência e contexto

- Roteamento por tarefa, capacidade, qualidade, latência e privacidade.
- Perfis de modelos sem limites artificiais de hardware.
- Fallbacks verificáveis entre engines e providers.
- Orçamento de contexto e compactação com preservação de fatos.
- Limites de turnos adaptativos com resposta final obrigatória.
- Detecção de loop e recuperação.
- Avaliações factuais, de código, ferramentas e tarefas longas.

## Gate J3 — Produto autônomo

- Interface localizada inicialmente em português e inglês.
- Explicações e ajuda contextual para cada função.
- Configuração guiada por perfis de execução.
- Estados de loading, erro, retomada e cancelamento claros.
- Desktop nativo, web e servidor reproduzíveis.
- Observabilidade, backup, exportação e atualização segura.

## Gate J4 — Agentes, memória e ferramentas

- Agentes persistentes com políticas e budgets.
- MCP e plugins com manifesto de capacidades.
- Memória separada do runtime de agentes.
- Fontes, proveniência, retenção e exclusão verificáveis.
- Filas duráveis para trabalhos longos.
- Testes contra efeitos duplicados e escalada de privilégios.

## Gate J5 — Compatibilidade Meta/Zane

- Schemas versionados para mensagens, tarefas, ferramentas, memória e eventos.
- SDK/adaptador de referência sem dependência da implementação interna.
- Suite de conformidade para Rachel.
- Exportação de configurações validada.
- Registro de decisões sobre o que será adaptado, reimplementado ou descartado.
- Gates `JARVIS_STANDALONE_READY` e `JARVIS_INTEGRATION_READY`.

## Critério de conclusão

Uma etapa só é concluída quando possui implementação, testes automatizados relevantes, validação do fluxo real, documentação e plano de reversão. Quantidade de recursos não substitui segurança, precisão ou rastreabilidade.

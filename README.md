# Sistema Inteligente de Gestão e Otimização de Espaços Corporativos

Protótipo funcional desenvolvido em regime de sprint de uma semana para a disciplina
**Qualidade e Testes de Sistemas Baseados em IA (ISTQB CT-AI)**.

Aloca automaticamente equipes de ~7.000 funcionários distribuídos em um prédio de
9 andares às salas mais adequadas, usando um motor de **otimização por restrições**
(Google OR-Tools CP-SAT), com explicabilidade, governança, observabilidade e
intervenção humana — não apenas "gerar qualquer alocação", mas produzir uma decisão
justificável e auditável.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend / API | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| Motor de otimização | Google OR-Tools (CP-SAT — programação por restrições) |
| Explicabilidade (IA) | Camada de NLG com fallback determinístico; usa Claude (Anthropic) se `ANTHROPIC_API_KEY` estiver configurada |
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 + Recharts |
| Testes | pytest + hypothesis (testes baseados em propriedades / metamórficos) |
| CI/CD | GitHub Actions |

## Como executar

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows (git-bash) — no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

A API sobe em `http://localhost:8000` e semeia automaticamente um cenário sintético
(9 andares, ~100 salas, 8 setores, ~60 equipes, incluindo um caso de exceção proposital)
na primeira execução. Documentação interativa em `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Sobe em `http://localhost:5173` e faz proxy de `/api/*` para o backend em `:8000`
(configurado em `frontend/vite.config.ts`).

### Rodar os testes

```bash
cd backend
source .venv/Scripts/activate
python -m pytest -v
```

## Arquitetura

```
/backend
  app/
    models.py         # Room, Sector, Team, ConstraintRule, AllocationRun, AllocationAssignment, AuditLog
    schemas.py         # contratos Pydantic da API
    seed.py             # gerador de dados sintéticos determinístico
    engine/
      candidates.py     # filtro de salas candidatas por equipe + causa raiz de eliminação
      allocation_engine.py  # modelo CP-SAT (motor de otimização) + persistência do resultado
      baseline.py       # estratégia "ingênua" (first-fit), usada só como referência "Antes"
    ai/
      explainer.py       # gera a justificativa em linguagem natural (com fallback)
    governance.py        # auditoria + métricas de observabilidade + dashboard
    routers/              # endpoints REST (rooms, sectors, teams, constraints, allocation, metrics, audit)
  tests/                 # testes automatizados, incluindo os metamórficos
/frontend
  src/
    pages/                # Dashboard, Alocação, Comparação, Setores, Salas, Monitoramento, Auditoria
    api/client.ts          # cliente HTTP tipado
    types.ts
/.github/workflows/ci.yml # pipeline de build + testes
```

## O motor de alocação

Modelado como um problema de **atribuição equipe → sala** em CP-SAT:

- **Restrições obrigatórias (hard)**: capacidade da sala ≥ tamanho da equipe, uma sala
  por equipe, uma equipe por sala, acessibilidade obrigatória, equipamento obrigatório,
  andar permitido, sala reservada para um setor específico, exclusão entre setores
  (não podem compartilhar andar).
- **Função objetivo (soft)**: maximiza o número de equipes alocadas, favorece maior
  % de ocupação da sala (minimiza ociosidade), pondera a prioridade da equipe, dá bônus
  por atender o andar preferido, e dá bônus por proximidade entre equipes relacionadas
  (medida como distância de andares via variáveis inteiras `floor_var` + `AddAbsEquality`).

Toda equipe que não recebe sala é reportada com a **causa raiz** específica (estágio do
filtro de candidatos em que o conjunto ficou vazio: capacidade, acessibilidade,
equipamento, andar permitido, reserva, ou concorrência por capacidade) — nunca
silenciosamente descartada.

## Critérios de aceitação

1. Nenhuma sala pode receber mais pessoas que sua capacidade (garantido pela modelagem
   CP-SAT e verificado por uma checagem de sanidade pós-solve; `AllocationRun.violations`
   deve ser sempre 0).
2. Nenhuma restrição obrigatória pode ser violada em uma recomendação aceita.
3. 100% das recomendações aceitas devem possuir justificativa estruturada + texto explicativo.
4. Toda equipe não alocada deve ter um motivo registrado (`reason_unallocated`).
5. Uma execução deve ser gerada dentro do limite de tempo definido pela equipe (5s para o
   cenário de ~60 equipes / ~100 salas — parametrizável via `time_limit_seconds`).
6. Uma nova execução não pode reduzir a taxa de alocação/ocupação da baseline manual sem
   justificativa registrada (ver tela de Comparação).

## Testes automatizados

`backend/tests/`:

- `test_capacity.py` — **Critério de aceitação #1** + **Teste metamórfico de propriedade**:
  nenhuma alocação pode exceder a capacidade da sala, verificado tanto no cenário
  sintético principal quanto em cenários aleatórios pequenos gerados via `hypothesis`
  (já que não conhecemos de antemão a alocação ótima para dezenas de equipes/salas).
- `test_metamorphic.py` — as 3 relações metamórficas da seção 15 do desafio:
  1. **Expansão de capacidade**: adicionar uma sala nunca reduz o nº de equipes alocadas.
  2. **Remoção de restrição**: desativar uma restrição obrigatória nunca reduz o nº de
     equipes alocadas.
  3. **Equipes equivalentes**: trocar os nomes de duas equipes com requisitos idênticos
     não altera significativamente a ocupação média da solução.
- `test_engine.py` — critérios de aceitação #3, #4 e #5 (justificativa presente, motivo
  registrado para não alocadas, tempo dentro do SLA) + campos de governança presentes.
- `test_api.py` — fluxo de ponta a ponta pela API (gerar → dashboard → comparação →
  aceitar recomendação → auditoria), evidência do protótipo funcional integrado.

## CI/CD

`.github/workflows/ci.yml` roda em todo push/PR:

1. Backend: instala dependências, valida o import da aplicação (build check), roda `pytest`.
2. Frontend: instala dependências (`npm ci`), checa tipos (`tsc --noEmit`), builda (`npm run build`).

## Explicabilidade

Cada recomendação aceita carrega um objeto estruturado (`justification`) e um texto em
linguagem natural (`explanation_text`), gerado por `app/ai/explainer.py`. Exemplo real
gerado pelo motor no cenário sintético:

> Sala 403 recomendada para Tecnologia - Equipe A. Capacidade da sala: 10 pessoas.
> Equipe: 10 pessoas. Ocupação prevista: 100.0%. Recursos necessários atendidos: sim.
> Acessibilidade: não exigida. Alternativas avaliadas: 29. Esta sala apresentou o
> melhor equilíbrio entre capacidade, localização e restrições dentre as alternativas
> disponíveis nesta execução.

Se `ANTHROPIC_API_KEY` estiver definida no ambiente, esse texto é gerado por um modelo
Claude a partir dos mesmos dados estruturados; caso contrário (ambiente offline, CI, ou
demo sem chave), um gerador determinístico baseado em template assume — o sistema nunca
fica sem explicação.

## Observabilidade

Tela **Monitoramento** (`/monitoramento`) e endpoint `GET /metrics/engine`: nº de
execuções, tempo da última/média execução, taxa média de alocação, ocupação média,
violações acumuladas, equipes não alocadas acumuladas, intervenções manuais, erros.

## Governança

Toda execução do motor gera um registro em `AllocationRun` (usuário, timestamp, versão
do algoritmo, equipes/salas analisadas, alocadas/não alocadas, violações, ocupação,
tempo de solve). Toda intervenção humana (aceitar/rejeitar/sobrescrever) é registrada em
`AuditLog`, visível na tela **Auditoria** (`/auditoria`) — permite responder depois:
quem executou, quando, com quais dados, qual versão do motor, e qual foi o resultado.

## Intervenção humana

Na tela **Gerar Alocação** (`/alocacao`), o Coordenador Geral pode, por recomendação:
**aceitar**, **rejeitar**, **alterar manualmente a sala**, ou **solicitar nova
otimização** (botão "Gerar Alocação Otimizada" novamente). Toda ação é auditada.

## Tratamento de exceções

O cenário sintético inclui de propósito uma equipe de 160 pessoas — maior que qualquer
sala do prédio (capacidade máxima: 150) — para demonstrar que o sistema identifica e
reporta a exceção (`ALERTA — Nenhuma sala com capacidade >= 160 pessoas.`) em vez de
alocá-la de forma inválida ou escondê-la. Visível na seção de alertas da tela de Alocação.

## Roteiro de demonstração

1. Abrir o Dashboard (ocupação inicial em 0%, nenhuma execução ainda).
2. Ir em Setores & Equipes, cadastrar/alterar uma equipe e uma restrição.
3. Ir em Salas, conferir o cadastro dos 9 andares.
4. Ir em Gerar Alocação → clicar em "GERAR ALOCAÇÃO OTIMIZADA".
5. Conferir a tabela de recomendações e clicar em "Ver justificativa" em uma linha.
6. Conferir a seção de alertas (equipe de 160 pessoas sem sala compatível).
7. Ir em Comparação — ver ocupação subir de ~58% para ~84% e assentos ociosos caírem.
8. Voltar ao Dashboard — indicadores atualizados por andar.
9. Ir em Monitoramento — tempo de solve, taxa de alocação, intervenções manuais.
10. Ir em Auditoria — histórico completo da execução e de qualquer aceite/rejeição/override.

## Por que confiar na recomendação?

Não porque "usamos IA" — porque:
- **Testes automatizados** garantem as propriedades de capacidade e as relações
  metamórficas (nova versão nunca piora silenciosamente).
- **Critérios de aceitação objetivos** definem o que é uma recomendação válida.
- **Explicabilidade** torna cada decisão auditável por um humano, não uma caixa-preta.
- **Observabilidade** expõe se o motor continua se comportando dentro do esperado em produção.
- **Governança** registra quem, quando, com quais dados e qual versão gerou cada resultado.
- **Intervenção humana** garante que a decisão final é sempre do Coordenador Geral — o
  sistema recomenda, não decide sozinho.

## Uso de IA no desenvolvimento

Este protótipo foi construído com apoio de IA (Claude/Claude Code) para acelerar
geração de boilerplate, modelagem do motor CP-SAT, componentes de frontend, testes
e configuração de CI/CD, conforme permitido e incentivado pelo desafio — mantendo a
responsabilidade da equipe sobre a corretude e explicação de cada decisão do sistema.

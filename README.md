# Analytics Consumer - Microserviço de Análise de Dados

## Visão Geral

O Analytics Consumer é um microserviço responsável por consumir eventos financeiros, de funcionários e alunos através de filas RabbitMQ e consolidar essas informações em um banco de dados analítico PostgreSQL. Atua como um hub central de processamento de métricas para toda a plataforma Fitcore.

## Arquitetura e Funcionamento

### Componentes Principais

1. **Consumers**: Processam eventos específicos das filas RabbitMQ
2. **Services**: Lógica de negócio para cálculos financeiros centralizados
3. **Models**: Estruturas de dados para diferentes entidades
4. **Utils**: Utilitários para processamento de datas e dados

### Fluxo de Dados

```
RabbitMQ Queues → Consumers → Services → PostgreSQL Analytics DB
```

## Responsabilidades por Domínio

### Dados Financeiros
- **Receitas**: Pagamentos de alunos, receitas diversas
- **Despesas**: Salários de funcionários, gastos operacionais
- **Cálculos**: Lucro líquido, margem de lucro, agregações mensais
- **Filas processadas**: 
  - `finance.expense.registered`
  - `finance.expense.deleted`
  - `employee-paid-queue`

### Dados de Funcionários
- **Cadastros**: Registro de novos funcionários
- **Atualizações**: Mudanças de cargo, status, demissões
- **Métricas**: Funcionários ativos, histórico de contratações
- **Filas processadas**: `analytics-cadastro-funcionario-queue`, `employee-dismissed-queue`

### Dados de Alunos
- **Matrículas**: Registro de novos alunos
- **Planos**: Mudanças de plano, status de atividade
- **Métricas**: Base de alunos ativos, tipos de plano
- **Filas processadas**: `cadastro-aluno-queue`, filas de mudanças de status

## Estrutura do Banco de Dados

### Tabela `profit`
Centraliza dados financeiros agregados por mês:
- Receitas totais mensais
- Despesas totais mensais
- Lucro líquido calculado
- Margem de lucro percentual
- Períodos de início e fim

### Tabelas de Entidades
- `students_registered`: Métricas de alunos
- `employees_registered`: Métricas de funcionários

## Importância no Ecossistema

### Para o Negócio
- **Visibilidade Financeira**: Consolida dados financeiros dispersos em uma visão unificada
- **Tomada de Decisão**: Fornece métricas em tempo real para gestão estratégica
- **Controle Operacional**: Monitora gastos, receitas e performance mensal automaticamente

### Para a Arquitetura
- **Desacoplamento**: Permite que outros serviços publiquem eventos sem se preocupar com analytics
- **Escalabilidade**: Processa eventos de forma assíncrona sem impactar performance dos serviços principais
- **Consistência**: Garante que todas as métricas sigam a mesma lógica de cálculo
- **Auditoria**: Mantém histórico completo de todas as transações e mudanças

### Para Outros Microserviços
- **API de Métricas**: Outros serviços podem consultar dados analíticos consolidados
- **Relatórios**: Base de dados preparada para dashboards e relatórios gerenciais
- **Alertas**: Pode disparar alertas baseados em métricas calculadas
- **Integração**: Facilita integração com ferramentas de BI e análise externa

## Configuração e Execução

### Variáveis de Ambiente
```
RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
DB_NAME, DB_USER, DB_PASS, DB_HOST
QUEUES (lista de filas para processar)
```

### Dependências
- RabbitMQ para mensageria
- PostgreSQL para persistência
- Python 3.x com bibliotecas: pika, psycopg2, python-dateutil

### Inicialização
O serviço automaticamente:
1. Conecta-se ao PostgreSQL e RabbitMQ
2. Cria tabelas necessárias
3. Inicia população com dados históricos (opcional)
4. Configura consumers para todas as filas definidas
5. Mantém escuta contínua dos eventos

## Benefícios Estratégicos

- **Centralização**: Um único ponto de verdade para métricas de negócio
- **Automação**: Cálculos financeiros automáticos eliminam trabalho manual
- **Tempo Real**: Métricas atualizadas conforme eventos acontecem
- **Histórico**: Preserva dados históricos para análises de tendência
- **Flexibilidade**: Fácil adição de novas métricas e cálculos
- **Confiabilidade**: Processamento robusto com tratamento de erros e rollback

Este microserviço é fundamental para transformar eventos operacionais em insights de negócio, fornecendo a base analítica necessária para o crescimento e gestão eficiente da plataforma Fitcore.

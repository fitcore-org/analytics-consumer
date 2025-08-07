-- =============================================
-- SCRIPT DE VERIFICAÇÃO DO CÁLCULO AUTOMÁTICO
-- Execute DEPOIS de rodar o test_auto_profit.sql
-- =============================================

-- 1. VERIFICAR SE A TABELA PROFITS FOI POPULADA AUTOMATICAMENTE
SELECT 
    'VERIFICAÇÃO: Lucros calculados automaticamente?' as status;

SELECT 
    TO_CHAR(period_start, 'MM/YYYY') as mes,
    CONCAT('R$ ', TO_CHAR(total_revenue, '999G999D90')) as receitas,
    CONCAT('R$ ', TO_CHAR(total_expenses, '999G999D90')) as gastos,
    CONCAT('R$ ', TO_CHAR(net_profit, '999G999D90')) as lucro,
    CONCAT(profit_margin, '%') as margem,
    CASE 
        WHEN net_profit > 0 THEN 'LUCRO'
        ELSE 'PREJUÍZO'
    END as resultado
FROM profits
WHERE period_start >= '2025-01-01'
ORDER BY period_start;

-- 2. CONTAR QUANTOS REGISTROS FORAM CRIADOS AUTOMATICAMENTE
SELECT 
    'Registros na tabela PROFITS' as info,
    COUNT(*) as quantidade_meses_calculados
FROM profits
WHERE period_start >= '2025-01-01';

-- 3. VERIFICAR SE OS VALORES ESTÃO CORRETOS
SELECT 
    'Conferência dos cálculos' as info;

-- Janeiro
SELECT 
    'Janeiro 2025' as mes,
    (SELECT SUM(amount) FROM revenues WHERE revenue_date >= '2025-01-01' AND revenue_date < '2025-02-01') as receitas_reais,
    (SELECT SUM(amount) FROM expenses WHERE expense_date >= '2025-01-01' AND expense_date < '2025-02-01') as gastos_reais,
    (SELECT total_revenue FROM profits WHERE period_start = '2025-01-01') as receitas_calculadas,
    (SELECT total_expenses FROM profits WHERE period_start = '2025-01-01') as gastos_calculados,
    CASE 
        WHEN (SELECT total_revenue FROM profits WHERE period_start = '2025-01-01') = 
             (SELECT SUM(amount) FROM revenues WHERE revenue_date >= '2025-01-01' AND revenue_date < '2025-02-01')
        THEN 'RECEITAS OK'
        ELSE 'RECEITAS INCORRETAS'
    END as status_receitas,
    CASE 
        WHEN (SELECT total_expenses FROM profits WHERE period_start = '2025-01-01') = 
             (SELECT SUM(amount) FROM expenses WHERE expense_date >= '2025-01-01' AND expense_date < '2025-02-01')
        THEN 'GASTOS OK'
        ELSE 'GASTOS INCORRETOS'
    END as status_gastos

UNION ALL

-- Fevereiro
SELECT 
    'Fevereiro 2025' as mes,
    (SELECT SUM(amount) FROM revenues WHERE revenue_date >= '2025-02-01' AND revenue_date < '2025-03-01') as receitas_reais,
    (SELECT SUM(amount) FROM expenses WHERE expense_date >= '2025-02-01' AND expense_date < '2025-03-01') as gastos_reais,
    (SELECT total_revenue FROM profits WHERE period_start = '2025-02-01') as receitas_calculadas,
    (SELECT total_expenses FROM profits WHERE period_start = '2025-02-01') as gastos_calculados,
    CASE 
        WHEN (SELECT total_revenue FROM profits WHERE period_start = '2025-02-01') = 
             (SELECT SUM(amount) FROM revenues WHERE revenue_date >= '2025-02-01' AND revenue_date < '2025-03-01')
        THEN 'RECEITAS OK'
        ELSE 'RECEITAS INCORRETAS'
    END as status_receitas,
    CASE 
        WHEN (SELECT total_expenses FROM profits WHERE period_start = '2025-02-01') = 
             (SELECT SUM(amount) FROM expenses WHERE expense_date >= '2025-02-01' AND expense_date < '2025-03-01')
        THEN 'GASTOS OK'
        ELSE 'GASTOS INCORRETOS'
    END as status_gastos;

-- 4. RESULTADO FINAL
SELECT 
    'RESULTADO DO TESTE' as resultado;

SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM profits WHERE period_start >= '2025-01-01') 
        THEN 'CÁLCULO AUTOMÁTICO FUNCIONANDO!'
        ELSE 'CÁLCULO AUTOMÁTICO NÃO FUNCIONOU'
    END as status_geral,
    
    CASE 
        WHEN (SELECT COUNT(*) FROM profits WHERE period_start >= '2025-01-01') >= 2
        THEN 'Múltiplos meses calculados'
        ELSE 'Apenas um mês calculado'
    END as status_multiplos_meses;

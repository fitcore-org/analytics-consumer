"""
Script para popular o banco com dados realísticos de negócio fitness

Este script cria dados sintéticos de lucros mensais seguindo a sazonalidade
específica de academias e aplicações fitness, incluindo:
- Picos em Janeiro (resoluções de ano novo) e Outubro (verão)
- Quedas em Junho (frio) e Dezembro (festas)
- Padrões realísticos de receita e despesas
"""

import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import random
from decimal import Decimal


def generate_sample_profit_data(cur, conn, months_back: int = 24) -> None:
    """
    Gera dados sintéticos de lucros mensais para negócio fitness
    
    Args:
        cur: Cursor do banco de dados
        conn: Conexão com o banco de dados
        months_back: Número de meses históricos para gerar (incluindo o mês atual)
    """
    
    print(f"🔄 Gerando {months_back} meses de dados fitness...")
    
    # Data atual (agosto 2025)
    current_month = date(2025, 8, 1)
    
    # Data de início (meses atrás a partir do mês atual)
    start_date = current_month - relativedelta(months=months_back-1)
    
    # Parâmetros para simulação realística de negócio fitness
    base_revenue = 8500   # Receita base mensal (mais conservador para fitness)
    base_expenses = 6200  # Despesas base mensal
    
    # Tendência de crescimento anual mais realista para fitness
    growth_rate = 0.08  # 8% ao ano (crescimento orgânico)
    monthly_growth = growth_rate / 12
    
    # Sazonalidade específica para negócio fitness
    seasonal_factors = {
        1: 1.4,   # Janeiro - Alta de matrículas (resoluções de ano novo)
        2: 1.2,   # Fevereiro - Continuação do impulso de janeiro
        3: 1.1,   # Março - Estabilização
        4: 1.0,   # Abril - Normal
        5: 1.0,   # Maio - Normal
        6: 0.8,   # Junho - Queda por causa do frio
        7: 1.1,   # Julho - Férias escolares, leve alta de matrículas
        8: 1.0,   # Agosto - Volta gradual das atividades
        9: 1.1,   # Setembro - Volta às atividades normais
        10: 1.3,  # Outubro - Início da busca por forma para o verão
        11: 1.2,  # Novembro - Black Friday (promoções), mantém alta
        12: 0.9   # Dezembro - Redução geral (festas e férias)
    }
    
    profits_data = []
    
    for i in range(months_back):
        # Data do período
        current_date = start_date + relativedelta(months=i)
        period_start = datetime(current_date.year, current_date.month, 1)
        
        # Último dia do mês
        if current_date.month == 12:
            period_end = datetime(current_date.year + 1, 1, 1) - relativedelta(days=1)
        else:
            period_end = datetime(current_date.year, current_date.month + 1, 1) - relativedelta(days=1)
        
        # Aplicar tendência de crescimento gradual
        growth_factor = 1 + (monthly_growth * i)
        
        # Aplicar sazonalidade específica do fitness
        seasonal_factor = seasonal_factors.get(current_date.month, 1.0)
        
        # Variabilidade mais controlada para negócio fitness (±15%)
        random_factor = random.uniform(0.85, 1.15)
        
        # Calcular receitas com padrões de academia/fitness
        monthly_revenue = base_revenue * growth_factor * seasonal_factor * random_factor
        
        # Despesas variam menos que receitas (custos mais fixos)
        expense_variability = random.uniform(0.92, 1.08)  # ±8% de variação
        monthly_expenses = base_expenses * growth_factor * expense_variability
        
        # Ajuste específico para meses de alta sazonalidade (mais custos operacionais)
        if seasonal_factor > 1.2:  # Janeiro e Outubro
            monthly_expenses *= 1.1  # 10% mais custos operacionais
        
        # Garantir margem mínima positiva
        if monthly_revenue <= monthly_expenses:
            monthly_expenses = monthly_revenue * 0.85  # Margem mínima de 15%
        
        net_profit = monthly_revenue - monthly_expenses
        profit_margin = (net_profit / monthly_revenue) * 100 if monthly_revenue > 0 else 0
        
        # Converter para Decimal para compatibilidade com PostgreSQL
        monthly_revenue = Decimal(str(round(monthly_revenue, 2)))
        monthly_expenses = Decimal(str(round(monthly_expenses, 2)))
        net_profit = Decimal(str(round(net_profit, 2)))
        profit_margin = Decimal(str(round(profit_margin, 2)))
        
        # Criar registro usando INSERT direto (compatível com sua estrutura)
        profit_data = {
            'id': str(uuid.uuid4()),
            'period_start': period_start,
            'period_end': period_end,
            'total_revenue': monthly_revenue,
            'total_expenses': monthly_expenses,
            'net_profit': net_profit,
            'profit_margin': profit_margin
        }
        
        profits_data.append(profit_data)
        
        # Adicionar emoji indicativo da sazonalidade
        season_emoji = "🔥" if seasonal_factors.get(current_date.month, 1.0) >= 1.3 else "📈" if seasonal_factors.get(current_date.month, 1.0) >= 1.1 else "📉" if seasonal_factors.get(current_date.month, 1.0) <= 0.9 else "📊"
        
        print(f"📅 {period_start.strftime('%Y-%m')} {season_emoji}: Receita: R$ {monthly_revenue:,.2f}, "
              f"Despesas: R$ {monthly_expenses:,.2f}, Lucro: R$ {net_profit:,.2f} (Margem: {profit_margin:.1f}%)")
    
    # Salvar no banco usando INSERT ON CONFLICT (compatível com sua aplicação)
    try:
        for profit in profits_data:
            cur.execute("""
                INSERT INTO profit (id, period_start, period_end, total_revenue, total_expenses, net_profit, profit_margin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (period_start, period_end) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_expenses = EXCLUDED.total_expenses,
                    net_profit = EXCLUDED.net_profit,
                    profit_margin = EXCLUDED.profit_margin,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                profit['id'],
                profit['period_start'],
                profit['period_end'],
                profit['total_revenue'],
                profit['total_expenses'],
                profit['net_profit'],
                profit['profit_margin']
            ))
        
        conn.commit()
        print(f"✅ {len(profits_data)} registros de lucros salvos com sucesso!")
        
        # Estatísticas detalhadas
        avg_revenue = sum(float(p['total_revenue']) for p in profits_data) / len(profits_data)
        avg_profit = sum(float(p['net_profit']) for p in profits_data) / len(profits_data)
        avg_margin = sum(float(p['profit_margin']) for p in profits_data) / len(profits_data)
        
        # Encontrar melhores e piores meses
        best_month = max(profits_data, key=lambda x: float(x['net_profit']))
        worst_month = min(profits_data, key=lambda x: float(x['net_profit']))
        
        print(f"\n📊 Estatísticas dos dados fitness gerados:")
        print(f"   • Receita média mensal: R$ {avg_revenue:,.2f}")
        print(f"   • Lucro médio mensal: R$ {avg_profit:,.2f}")
        print(f"   • Margem de lucro média: {avg_margin:.1f}%")
        print(f"   • Melhor mês: {best_month['period_start'].strftime('%Y-%m')} (R$ {best_month['net_profit']:,.2f})")
        print(f"   • Pior mês: {worst_month['period_start'].strftime('%Y-%m')} (R$ {worst_month['net_profit']:,.2f})")
        print(f"   • Período: {profits_data[0]['period_start'].strftime('%Y-%m')} até {profits_data[-1]['period_end'].strftime('%Y-%m')}")
        print(f"\n🏋️  Sazonalidade fitness aplicada:")
        print(f"   🔥 Picos: Janeiro (Resoluções), Outubro (Verão)")
        print(f"   📉 Baixas: Junho (Frio), Dezembro (Festas)")
        print(f"   🎯 Inclui mês atual: Agosto 2025")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar dados: {e}")
        raise


def clear_existing_data(cur, conn):
    """
    Limpa dados existentes de lucros
    """
    try:
        # Remove todos os registros existentes
        cur.execute("DELETE FROM profit")
        conn.commit()
        print("🗑️  Dados existentes removidos")
        
    except Exception as e:
        print(f"❌ Erro ao limpar dados: {e}")
        conn.rollback()
        raise


def check_existing_data(cur):
    """
    Verifica se já existem dados na tabela profit
    """
    try:
        cur.execute("SELECT COUNT(*) FROM profit")
        count = cur.fetchone()[0]
        return count
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados existentes: {e}")
        return 0


def populate_profit_if_empty(cur, conn, months_back: int = 24):
    """
    Popula a tabela profit apenas se ela estiver vazia
    Função otimizada para ser chamada durante a inicialização da aplicação
    """
    try:
        existing_count = check_existing_data(cur)
        
        if existing_count == 0:
            print("📈 Tabela profit vazia, iniciando população com dados sintéticos...")
            generate_sample_profit_data(cur, conn, months_back)
            print("✅ População automática concluída!")
        else:
            print(f"📊 Tabela profit já contém {existing_count} registros, pulando população automática")
            
    except Exception as e:
        print(f"❌ Erro durante população automática: {e}")
        # Não propagar o erro para não quebrar a aplicação principal


if __name__ == "__main__":
    import psycopg2
    
    # Configuração do banco (deve vir de variáveis de ambiente em produção)
    DB_CONFIG = {
        "dbname": "analytics_db",
        "user": "analytics_user",
        "password": "analytics_pass",
        "host": "localhost",
        "port": 5432
    }
    
    print("🏋️  Iniciando população do banco com dados fitness realísticos...")
    print("📅 Incluindo período até Agosto 2025 (mês atual)")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Verificar se já existem dados
        existing_count = check_existing_data(cur)
        if existing_count > 0:
            print(f"⚠️  Encontrados {existing_count} registros existentes na tabela profit")
            response = input("Deseja limpar dados existentes? (s/n): ").lower().strip()
            if response in ['s', 'sim', 'y', 'yes']:
                clear_existing_data(cur, conn)
        
        # Gera novos dados
        try:
            months_input = input("Quantos meses de histórico gerar? (padrão: 24): ").strip()
            months = int(months_input) if months_input else 24
            generate_sample_profit_data(cur, conn, months_back=months)
            
            print("\n✨ População do banco concluída com sazonalidade fitness!")
            
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário")
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        if 'conn' in locals():
            try:
                cur.close()
                conn.close()
            except:
                pass

import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

class FinancialService:
    def __init__(self, cursor, connection):
        self.cur = cursor
        self.conn = connection
        self._create_tables()
    
    def _create_tables(self):
        """Cria a tabela financeira centralizada"""
        
        # Tabela única de lucros/perdas (centralizada)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS profit (
                id UUID PRIMARY KEY,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                total_revenue DECIMAL(12,2) NOT NULL DEFAULT 0,
                total_expenses DECIMAL(12,2) NOT NULL DEFAULT 0,
                net_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
                profit_margin DECIMAL(8,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(period_start, period_end)
            );
        """)
        
        self.conn.commit()
        print("[✔] Tabela financeira centralizada criada com sucesso")
    
    def add_expense(self, amount: Decimal, description: str, expense_date: Optional[datetime] = None) -> str:
        """Adiciona um gasto diretamente na tabela profit"""
        transaction_date = expense_date or datetime.now()
        
        # Atualizar/criar registro do mês
        self._update_monthly_profit(transaction_date, expense_amount=amount)
        
        # Retornar ID único para tracking
        return str(uuid.uuid4())
    
    def add_revenue(self, amount: Decimal, description: str, revenue_date: Optional[datetime] = None) -> str:
        """Adiciona uma receita diretamente na tabela profit"""
        transaction_date = revenue_date or datetime.now()
        
        # Atualizar/criar registro do mês
        self._update_monthly_profit(transaction_date, revenue_amount=amount)
        
        # Retornar ID único para tracking
        return str(uuid.uuid4())
    
    def _update_monthly_profit(self, transaction_date: datetime, revenue_amount: Optional[Decimal] = None, expense_amount: Optional[Decimal] = None):
        """Atualiza o lucro mensal diretamente na tabela profit"""
        # Calcula o início e fim do mês
        period_start = transaction_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if period_start.month == 12:
            next_month = period_start.replace(year=period_start.year + 1, month=1)
        else:
            next_month = period_start.replace(month=period_start.month + 1)
        
        period_end = next_month - timedelta(seconds=1)
        
        # Verificar se já existe registro para este mês
        self.cur.execute("""
            SELECT total_revenue, total_expenses FROM profit 
            WHERE period_start = %s AND period_end = %s
        """, (period_start, period_end))
        
        existing = self.cur.fetchone()
        
        if existing:
            # Atualizar registro existente
            current_revenue, current_expenses = existing
            
            # Somar os novos valores
            new_revenue = current_revenue + (revenue_amount or Decimal('0'))
            new_expenses = current_expenses + (expense_amount or Decimal('0'))
            
            net_profit = new_revenue - new_expenses
            
            # Calcular margem de lucro
            if new_revenue > 0:
                profit_margin = (net_profit / new_revenue * 100)
                profit_margin = max(-99999.99, min(99999.99, profit_margin))
            else:
                profit_margin = 0
            
            self.cur.execute("""
                UPDATE profit SET 
                    total_revenue = %s,
                    total_expenses = %s,
                    net_profit = %s,
                    profit_margin = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE period_start = %s AND period_end = %s
            """, (new_revenue, new_expenses, net_profit, profit_margin, period_start, period_end))
            
        else:
            # Criar novo registro
            new_revenue = revenue_amount or Decimal('0')
            new_expenses = expense_amount or Decimal('0')
            net_profit = new_revenue - new_expenses
            
            # Calcular margem de lucro
            if new_revenue > 0:
                profit_margin = (net_profit / new_revenue * 100)
                profit_margin = max(-99999.99, min(99999.99, profit_margin))
            else:
                profit_margin = 0
            
            self.cur.execute("""
                INSERT INTO profit (id, period_start, period_end, total_revenue, total_expenses, net_profit, profit_margin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (str(uuid.uuid4()), period_start, period_end, new_revenue, new_expenses, net_profit, profit_margin))
        
        self.conn.commit()
        
        # Log do resultado
        final_revenue = new_revenue
        final_expenses = new_expenses
        final_profit = final_revenue - final_expenses
        
        print(f"[✔] Lucro mensal atualizado: {period_start.strftime('%Y-%m')} | Receitas: R$ {final_revenue} | Gastos: R$ {final_expenses} | Lucro: R$ {final_profit}")
    
    def get_monthly_summary(self, year: int, month: int) -> dict:
        """Retorna resumo financeiro de um mês específico"""
        period_start = datetime(year, month, 1)
        
        if month == 12:
            next_month = period_start.replace(year=year + 1, month=1)
        else:
            next_month = period_start.replace(month=month + 1)
        
        period_end = next_month - timedelta(seconds=1)
        
        self.cur.execute("""
            SELECT total_revenue, total_expenses, net_profit, profit_margin
            FROM profit 
            WHERE period_start = %s AND period_end = %s
        """, (period_start, period_end))
        
        result = self.cur.fetchone()
        if result:
            return {
                "total_revenue": float(result[0]),
                "total_expenses": float(result[1]),
                "net_profit": float(result[2]),
                "profit_margin": float(result[3])
            }
        return {
            "total_revenue": 0,
            "total_expenses": 0,
            "net_profit": 0,
            "profit_margin": 0
        }
    
    def get_last_months_summary(self, months: int = 6) -> List[dict]:
        """Retorna resumo dos últimos N meses"""
        self.cur.execute("""
            SELECT period_start, total_revenue, total_expenses, net_profit, profit_margin
            FROM profit 
            ORDER BY period_start DESC 
            LIMIT %s
        """, (months,))
        
        results = []
        for row in self.cur.fetchall():
            results.append({
                "month": row[0].strftime("%Y-%m"),
                "total_revenue": float(row[1]),
                "total_expenses": float(row[2]),
                "net_profit": float(row[3]),
                "profit_margin": float(row[4])
            })
        
        return results

import json
import requests
from decimal import Decimal
from datetime import datetime
from utils.date_utils import parse_datetime

def finance_expense_registered_callback(ch, method, properties, body, cur, conn):
    """Processa eventos de gastos registrados da fila finance.expense.registered"""
    try:
        data = json.loads(body)
        payload = data.get('payload', {})
        
        amount = Decimal(str(payload.get('amount', '0')))
        category = payload.get('category', '')
        description = payload.get('description', 'Gasto operacional')
        date_str = payload.get('date', datetime.now().isoformat())
        responsible = payload.get('responsible', '')
        
        # Parsear data ISO
        expense_date = parse_datetime(date_str)
        
        # Enriquecer descrição com categoria e responsável
        if category:
            description = f"{category} - {description}"
        if responsible:
            description += f" (Resp: {responsible})"
        
        # Adicionar gasto ao sistema financeiro
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_expense(amount, description, expense_date)
        
        print(f"[✔] Gasto registrado: R$ {amount} - {description}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar gasto registrado: {e}")
        conn.rollback()

def finance_expense_deleted_callback(ch, method, properties, body, cur, conn):
    """Processa eventos de exclusão de gastos da fila finance.expense.deleted"""
    try:
        data = json.loads(body)
        payload = data.get('payload', {})
        
        expense_id = payload.get('id')
        deleted_at = payload.get('deleted_at')
        
        print(f"[ℹ] Gasto {expense_id} foi excluído em {deleted_at}")
        print(f"[!] Nota: Sistema centralizado não remove gastos individuais, apenas recalcula totais mensais")
        
    except Exception as e:
        print(f"[✖] Erro ao processar exclusão de gasto: {e}")

def employee_paid_queue_callback(ch, method, properties, body, cur, conn):
    """Processa pagamentos de funcionários da fila employee-paid-queue"""
    try:
        data = json.loads(body)
        
        employee_id = data.get('id')
        amount = Decimal(str(data.get('amount', '0')))
        month = data.get('month')
        year = data.get('year')
        paid_at = data.get('paid_at')
        
        # Parsear timestamp do pagamento
        payment_date = parse_datetime(paid_at)
        
        # Construir descrição
        description = f"Salário {month}/{year} - Funcionário {employee_id}"
        
        # Adicionar gasto ao sistema financeiro
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_expense(amount, description, payment_date)
        
        print(f"[✔] Pagamento funcionário processado: R$ {amount} - {description}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar pagamento de funcionário: {e}")
        conn.rollback()

def employee_dismissed_queue_callback(ch, method, properties, body, cur, conn):
    """Processa demissões de funcionários da fila employee-dismissed-queue"""
    try:
        data = json.loads(body)
        payload = data.get('payload', {})
        
        employee_id = payload.get('employee_id')
        dismissed_at = payload.get('dismissed_at')
        
        # Parsear data da demissão
        dismissal_date = parse_datetime(dismissed_at)
        
        print(f"[ℹ] Funcionário {employee_id} foi demitido em {dismissal_date}")
        
        # Marcar como inativo na tabela de funcionários
        cur.execute("""
            UPDATE employees_registered 
            SET active = false, termination_date = %s 
            WHERE id = %s
        """, (dismissal_date, employee_id))
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"[✔] Funcionário {employee_id} marcado como demitido")
        else:
            print(f"[!] Funcionário {employee_id} não encontrado na base de dados")
        
    except Exception as e:
        print(f"[✖] Erro ao processar demissão de funcionário: {e}")
        conn.rollback()

def plan_subscription_paid_callback(ch, method, properties, body, cur, conn):
    """Processa pagamentos de assinaturas de planos da fila plan-subscription-paid"""
    try:
        data = json.loads(body)
        
        plan_id = data.get('planId')
        installments = data.get('installments', 1)
        customer_id = data.get('customerId')
        
        if not plan_id:
            print(f"[!] planId não encontrado no payload")
            return
        
        # Fazer GET para obter informações do plano
        try:
            response = requests.get(f"http://localhost:8080/payment/api/plans/{plan_id}")
            response.raise_for_status()
            plan_data = response.json()
            
            # Extrair o preço do primeiro item do plano
            items = plan_data.get('items', [])
            if not items:
                print(f"[!] Nenhum item encontrado no plano {plan_id}")
                return
            
            pricing_scheme = items[0].get('pricingScheme', {})
            price_in_cents = pricing_scheme.get('price', 0)
            
            if price_in_cents == 0:
                print(f"[!] Preço não encontrado para o plano {plan_id}")
                return
            
            # Converter centavos para reais
            total_price = Decimal(str(price_in_cents)) / Decimal('100')
            
            # Calcular valor por parcela
            installment_value = total_price / Decimal(str(installments))
            
            # Obter a data atual para registrar a receita
            payment_date = datetime.now()
            
            # Construir descrição
            plan_name = plan_data.get('name', f'Plano {plan_id}')
            description = f"Assinatura {plan_name} - Cliente {customer_id}"
            if installments > 1:
                description += f" (1/{installments} parcelas)"
            
            # Adicionar receita ao sistema financeiro
            from services.financial_service import FinancialService
            financial_service = FinancialService(cur, conn)
            financial_service.add_revenue(installment_value, description, payment_date)
            
            print(f"[✔] Assinatura processada: R$ {installment_value} - {description}")
            print(f"[ℹ] Preço total: R$ {total_price}, Parcelas: {installments}")
            
        except requests.RequestException as e:
            print(f"[✖] Erro ao buscar informações do plano {plan_id}: {e}")
            conn.rollback()
            
    except Exception as e:
        print(f"[✖] Erro ao processar assinatura de plano: {e}")
        conn.rollback()

# ===== CALLBACKS LEGACY (MANTIDOS PARA COMPATIBILIDADE) =====

def expense_added_callback(ch, method, properties, body, cur, conn):
    """Callback legado para gastos gerais"""
    try:
        data = json.loads(body)
        amount = Decimal(str(data.get('amount', 0)))
        description = data.get('description', 'Gasto operacional')
        expense_date = parse_datetime(data.get('expense_date', datetime.now().isoformat()))
        
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_expense(amount, description, expense_date)
        
        print(f"[✔] Gasto adicionado: R$ {amount} - {description}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar gasto: {e}")

def revenue_added_callback(ch, method, properties, body, cur, conn):
    """Callback legado para receitas gerais"""
    try:
        data = json.loads(body)
        amount = Decimal(str(data.get('amount', 0)))
        description = data.get('description', 'Receita geral')
        revenue_date = parse_datetime(data.get('revenue_date', datetime.now().isoformat()))
        
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_revenue(amount, description, revenue_date)
        
        print(f"[✔] Receita adicionada: R$ {amount} - {description}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar receita: {e}")

def student_payment_callback(ch, method, properties, body, cur, conn):
    """Callback legado para pagamentos de alunos"""
    try:
        data = json.loads(body)
        amount = Decimal(str(data.get('amount', 0)))
        description = f"Mensalidade - {data.get('student_name', 'Aluno')}"
        payment_date = parse_datetime(data.get('payment_date', datetime.now().isoformat()))
        
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_revenue(amount, description, payment_date)
        
        print(f"[✔] Pagamento de aluno processado: R$ {amount}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar pagamento de aluno: {e}")

def employee_payment_callback(ch, method, properties, body, cur, conn):
    """Callback legado para pagamentos de funcionários"""
    try:
        data = json.loads(body)
        amount = Decimal(str(data.get('amount', 0)))
        description = f"Salário - {data.get('employee_name', 'Funcionário')}"
        payment_date = parse_datetime(data.get('payment_date', datetime.now().isoformat()))
        
        from services.financial_service import FinancialService
        financial_service = FinancialService(cur, conn)
        financial_service.add_expense(amount, description, payment_date)
        
        print(f"[✔] Pagamento de funcionário processado: R$ {amount}")
        
    except Exception as e:
        print(f"[✖] Erro ao processar pagamento de funcionário: {e}")

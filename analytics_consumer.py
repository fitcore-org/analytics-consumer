import pika
import psycopg2
import os
import time
import functools
import signal
import sys
from pika.exceptions import AMQPConnectionError

from consumers.student_consumer import (
    student_register_callback,
    student_plan_changed_callback,
    student_status_changed_callback,
    student_deleted_callback,
)
from consumers.employee_consumer import (
    employee_register_callback,
    employee_role_changed_callback,
    employee_status_changed_callback,
    employee_deleted_callback,
)
from consumers.financial_consumer import (
    # Novos consumidores para filas reais
    finance_expense_registered_callback,
    finance_expense_deleted_callback,
    employee_paid_queue_callback,
    employee_dismissed_queue_callback,
    # Callbacks legados (mantidos para compatibilidade)
    expense_added_callback,
    revenue_added_callback,
    student_payment_callback,
    employee_payment_callback,
)
from services.financial_service import FinancialService

# Variáveis de ambiente vindas do Docker
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")

QUEUES = os.getenv("QUEUES", "cadastro-aluno-queue," \
                    "analytics-cadastro-funcionario-queue," \
                    "analytics-student-deleted-queue," \
                    "analytics-employee-deleted-queue," \
                    "analytics-employee-status-changed-queue," \
                    "finance.expense.registered," \
                    "finance.expense.deleted," \
                    "employee-paid-queue," \
                    "employee-dismissed-queue," \
                    "expense-added-queue," \
                    "revenue-added-queue," \
                    "student-payment-queue," \
                    "employee-payment-queue").split(",")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "analytics_db"),  
    "user": os.getenv("DB_USER", "analytics_user"),        
    "password": os.getenv("DB_PASS", "analytics_pass"),   
    "host": os.getenv("DB_HOST", "localhost"),
    "port": 5433
}

# Conexão com PostgreSQL e criação das tabelas
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("[✔] Conectado ao PostgreSQL")
    
    # Inicializar serviço financeiro (cria as tabelas automaticamente)
    financial_service = FinancialService(cur, conn)
    print("[✔] Serviço financeiro inicializado")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students_registered (
            id UUID PRIMARY KEY,
            plan_type VARCHAR(30),
            active BOOLEAN,
            registration_date TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees_registered (
            id UUID PRIMARY KEY,
            role VARCHAR(30),
            active BOOLEAN,
            registration_date TIMESTAMP,
            last_update_date TIMESTAMP,
            termination_date TIMESTAMP
        );
    """)
    conn.commit()
    print("[✔] Tabelas analíticas prontas.")
    
    # População automática da tabela profit (se necessário)
    try:
        from seed.auto_populate import auto_populate_profit_data
        auto_populate_profit_data(cur, conn)
    except Exception as e:
        print(f"[⚠] Aviso: Erro na população automática: {e}")
        print("[ℹ] A aplicação continuará normalmente")
        
except Exception as e:
    print("[✖] Erro ao conectar ao PostgreSQL:", e)
    exit(1)

# Conexão com RabbitMQ (com tentativas)
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)

for i in range(10):
    try:
        connection = pika.BlockingConnection(parameters)
        print("[✔] Conectado ao RabbitMQ")
        break
    except AMQPConnectionError:
        print(f"[!] Tentativa {i+1}/10: RabbitMQ indisponível. Tentando novamente em 5s...")
        time.sleep(5)
else:
    print("Não foi possível conectar ao RabbitMQ após 10 tentativas.")
    exit(1)

channel = connection.channel()

# Função para graceful shutdown
def signal_handler(signum, frame):
    """Trata o sinal de interrupção (Ctrl+C)"""
    print("\n[ℹ] Sinal de interrupção recebido. Encerrando todas as conexões...")
    
    try:
        # Para o consumo de mensagens
        if channel and not channel.is_closed:
            print("[→] Parando o consumo de mensagens...")
            channel.stop_consuming()
        
        # Fecha a conexão com RabbitMQ
        if connection and not connection.is_closed:
            print("[→] Fechando conexão com RabbitMQ...")
            connection.close()
        
        # Fecha a conexão com PostgreSQL
        if cur and not cur.closed:
            cur.close()
        if conn and not conn.closed:
            print("[→] Fechando conexão com PostgreSQL...")
            conn.close()
            
        print("[✔] Aplicação encerrada com sucesso!")
        
    except Exception as e:
        print(f"[⚠] Erro durante o encerramento: {e}")
    
    finally:
        sys.exit(0)

# Registra o handler para SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# Mapeamento de callbacks por fila
CALLBACKS = {
    # Filas de estudantes
    "cadastro-aluno-queue": student_register_callback,
    "student-plan-changed-queue": student_plan_changed_callback,
    "student-status-changed-queue": student_status_changed_callback,
    "analytics-student-deleted-queue": student_deleted_callback, # Fila nova
    
    # Filas de funcionários
    "analytics-cadastro-funcionario-queue": employee_register_callback, # Fila nova
    "employee-role-changed-queue": employee_role_changed_callback,
    "analytics-employee-deleted-queue": employee_deleted_callback, # Fila nova
    
    # Novas filas financeiras reais
    "employee-status-changed-queue": employee_status_changed_callback,
    "finance.expense.registered": finance_expense_registered_callback,
    "finance.expense.deleted": finance_expense_deleted_callback,
    "employee-paid-queue": employee_paid_queue_callback,
    "employee-dismissed-queue": employee_dismissed_queue_callback,
    
    # Filas legadas (compatibilidade)
    "expense-added-queue": expense_added_callback,
    "revenue-added-queue": revenue_added_callback,
    "student-payment-queue": student_payment_callback,
    "employee-payment-queue": employee_payment_callback,
}

for queue in QUEUES:
    queue = queue.strip()
    channel.queue_declare(queue=queue, durable=True)
    if queue in CALLBACKS:
        callback = CALLBACKS[queue]
        # Use partial para fixar queue, cur e conn
        channel.basic_consume(
            queue=queue,
            on_message_callback=functools.partial(callback, cur=cur, conn=conn),
            auto_ack=True
        )
    else:
        print(f"[!] Nenhum callback definido para a fila '{queue}'.")

print("[→] Escutando as filas analíticas...")
print("[ℹ] Pressione Ctrl+C para encerrar a aplicação de forma segura")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    # Isso nunca deveria ser alcançado devido ao signal handler, 
    # mas é uma boa prática ter como fallback
    print("\n[ℹ] Interrupção detectada. Encerrando...")
    signal_handler(None, None)
except Exception as e:
    print(f"[✖] Erro inesperado durante o consumo: {e}")
    # Tenta fazer cleanup mesmo em caso de erro
    signal_handler(None, None)
import pika
import psycopg2
import os
import time
import functools
from pika.exceptions import AMQPConnectionError
from utils.date_utils import parse_datetime

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

# Variáveis de ambiente vindas do Docker
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

QUEUES = os.getenv("QUEUES", "cadastro-aluno-queue,cadastro-funcionario-queue").split(",")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": os.getenv("DB_HOST"),
    "port": 5432
}

# Conexão com PostgreSQL e criação das tabelas
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("[✔] Conectado ao PostgreSQL")
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
            registration_date TIMESTAMP
        );
    """)
    conn.commit()
    print("[✔] Tabelas analíticas prontas.")
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

# Mapeamento de callbacks por fila
CALLBACKS = {
    "cadastro-aluno-queue": student_register_callback,
    "cadastro-funcionario-queue": employee_register_callback,
    "student-plan-changed-queue": student_plan_changed_callback,
    "student-status-changed-queue": student_status_changed_callback,
    "student-deleted-queue": student_deleted_callback,
    "employee-role-changed-queue": employee_role_changed_callback,
    "employee-status-changed-queue": employee_status_changed_callback,
    "employee-deleted-queue": employee_deleted_callback,
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
channel.start_consuming()
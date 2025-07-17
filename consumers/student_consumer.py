import json
from utils.date_utils import parse_datetime

def student_register_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute("""
            INSERT INTO students_registered (
                id, plan_type, active, registration_date
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            data["id"],
            data["planType"],
            data["active"],
            parse_datetime(data.get("registrationDate"))
        ))
        conn.commit()
        print(f"[✔] Métrica de aluno '{data['id']}' inserida.")
    except Exception as e:
        print("[✖] Erro ao inserir aluno:", e)
        conn.rollback()

def student_plan_changed_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute(
            "UPDATE students_registered SET plan_type=%s, active=%s WHERE id=%s",
            (data["planType"], data["active"], data["id"])
        )
        if "lastUpdateDate" in data:
            cur.execute(
                "UPDATE students_registered SET last_update_date=%s WHERE id=%s",
                (parse_datetime(data["lastUpdateDate"]), data["id"])
            )
        conn.commit()
        print(f"[✔] Plano do aluno '{data['id']}' atualizado.")
    except Exception as e:
        print("[✖] Erro ao processar mudança de plano do aluno:", e)
        conn.rollback()

def student_status_changed_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute(
            "UPDATE students_registered SET active=%s WHERE id=%s",
            (data["active"], data["id"])
        )
        conn.commit()
        print(f"[✔] Status do aluno '{data['id']}' atualizado.")
    except Exception as e:
        print("[✖] Erro ao processar mudança de status do aluno:", e)
        conn.rollback()

def student_deleted_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        student_id = data.get("studentId") or data.get("id")
        cur.execute(
            "DELETE FROM students_registered WHERE id=%s",
            (student_id,)
        )
        conn.commit()
        print(f"[✔] Aluno '{student_id}' removido.")
    except Exception as e:
        print("[✖] Erro ao processar exclusão de aluno:", e)
        conn.rollback()
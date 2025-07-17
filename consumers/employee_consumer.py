import json
from utils.date_utils import parse_datetime

def employee_register_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute("""
            INSERT INTO employees_registered (
                id, role, active, registration_date
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            data["id"],
            data["role"],
            data["active"],
            parse_datetime(data.get("registrationDate"))
        ))
        conn.commit()
        print(f"[✔] Métrica de funcionário '{data['id']}' inserida.")
    except Exception as e:
        print("[✖] Erro ao inserir funcionário:", e)
        conn.rollback()

def employee_role_changed_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute(
            "UPDATE employees_registered SET role=%s, active=%s WHERE id=%s",
            (data["role"], data["active"], data["id"])
        )
        if "lastUpdateDate" in data:
            cur.execute(
                "UPDATE employees_registered SET last_update_date=%s WHERE id=%s",
                (parse_datetime(data["lastUpdateDate"]), data["id"])
            )
        conn.commit()
        print(f"[✔] Cargo do funcionário '{data['id']}' atualizado.")
    except Exception as e:
        print("[✖] Erro ao processar mudança de cargo do funcionário:", e)
        conn.rollback()

def employee_status_changed_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        cur.execute(
            "UPDATE employees_registered SET active=%s WHERE id=%s",
            (data["active"], data["id"])
        )
        conn.commit()
        print(f"[✔] Status do funcionário '{data['id']}' atualizado.")
    except Exception as e:
        print("[✖] Erro ao processar mudança de status do funcionário:", e)
        conn.rollback()

def employee_deleted_callback(ch, method, properties, body, cur, conn):
    try:
        data = json.loads(body)
        employee_id = data.get("employeeId") or data.get("id")
        cur.execute(
            "DELETE FROM employees_registered WHERE id=%s",
            (employee_id,)
        )
        conn.commit()
        print(f"[✔] Funcionário '{employee_id}' removido.")
    except Exception as e:
        print("[✖] Erro ao processar exclusão de funcionário:", e)
        conn.rollback()
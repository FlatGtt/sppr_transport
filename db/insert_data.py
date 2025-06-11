import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import random
from db.database import get_connection

def insert_data():
    df = pd.read_csv("data/failures_real.csv") 

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM events;")
    cur.execute("DELETE FROM objects;")
    conn.commit()


    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO objects (id, type, mtbf, mttr, last_failure_date, availability)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(row["id"]),
            row["type"],
            float(row["mtbf"]),
            float(row["mttr"]),
            row["last_failure_date"],
            round(float(row["mtbf"]) / (float(row["mtbf"]) + float(row["mttr"])), 4)
        ))

    conn.commit()

    # ⚙️ Генерация событий (отказов и ремонтов)
    simulation_hours = 720  # 30 дней
    event_id = 1

    for _, row in df.iterrows():
        obj_id = int(row["id"])
        mtbf = float(row["mtbf"])
        mttr = float(row["mttr"])

        t = 0
        while t < simulation_hours:
            failure_time = random.expovariate(1 / mtbf)
            t += failure_time
            if t >= simulation_hours:
                break

            cur.execute("""
                INSERT INTO events (id, object_id, event_type, time)
                VALUES (%s, %s, %s, %s)
            """, (event_id, obj_id, "failure", round(t, 2)))
            event_id += 1

            # Ремонт сразу после отказа
            repair_time = t + mttr
            if repair_time < simulation_hours:
                cur.execute("""
                    INSERT INTO events (id, object_id, event_type, time)
                    VALUES (%s, %s, %s, %s)
                """, (event_id, obj_id, "repair", round(repair_time, 2)))
                event_id += 1

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Данные успешно добавлены.")

if __name__ == "__main__":
    insert_data()

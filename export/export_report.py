import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from db.database import get_connection

def export_report():
    conn = get_connection()

    # Загружаем данные из БД
    df_objects = pd.read_sql("SELECT * FROM objects ORDER BY id", conn)
    df_events = pd.read_sql("SELECT * FROM events ORDER BY object_id, time", conn)

    # Сводка по отказам и ремонтам
    summary = df_events.groupby(['object_id', 'event_type']).size().unstack(fill_value=0).reset_index()
    summary.columns.name = None  # убрать имя индекса

    # Объединяем с объектами
    report = pd.merge(df_objects, summary, left_on='id', right_on='object_id', how='left')
    report = report.drop(columns=['object_id'])

    # Записываем в Excel
    with pd.ExcelWriter("report.xlsx", engine='openpyxl') as writer:
        df_objects.to_excel(writer, sheet_name='Объекты', index=False)
        df_events.to_excel(writer, sheet_name='События', index=False)
        report.to_excel(writer, sheet_name='Аналитика', index=False)

    conn.close()
    print("✅ Отчёт 'report.xlsx' успешно сформирован.")

if __name__ == "__main__":
    export_report()

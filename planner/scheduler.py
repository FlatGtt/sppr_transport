def plan_repairs(mtbf, mttr, period=720):
    """
    Строит график ППР. Возвращает список пар: (время ремонта, длительность)
    """
    repairs = []
    time = 0
    while time < period:
        time += mtbf
        repairs.append((round(time, 2), mttr))
    return repairs

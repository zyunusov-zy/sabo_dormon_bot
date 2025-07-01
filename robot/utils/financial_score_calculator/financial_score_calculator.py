from datetime import datetime

def calculate_final_conclusion(data: dict) -> dict:
    def _calculate_income_points(income: str) -> int:
        income = income.lower()
        if 'до 5 млн' in income:
            return 2
        elif '5-7 млн' in income:
            return 1
        return 0

    def _calculate_children_points(children: str) -> int:
        print("[DEBUG] CHILDREN: ", children)
        try:
            if children == "5+":
                return 2
            elif children == "3" or children == "4":
                return 1
        except:
            pass
        return 0

    def _calculate_work_points(work: str) -> int:
        work = work.strip().lower()
        if "никто" in work:
            return 2
        elif "только муж" in work or "только жена" in work:
            return 1
        return 0


    def _calculate_housing_points(house: str) -> int:
        house = house.lower()
        return 1 if '☑️ аренда' in house else 0

    # def _calculate_treatment_importance_points(comment: str) -> int:
    #     comment = comment.lower()
    #     if 'жуда мухим' in comment:
    #         return 2
    #     elif 'мухим' in comment:
    #         return 1
    #     return 0

    def _calculate_mahalla_points(confirmed: str) -> int:
        return 1 if confirmed.strip().lower() in ['ҳа', '☑️ Да, есть'] else 0

    def determine_support_level(score: int) -> dict:
        if score >= 6:
            return {'category': '80% помощь (6–10 баллов)', 'fund_help': '80%', 'sabo_discount': '20%', 'patient_payment': '0–20%'}
        elif score >= 4:
            return {'category': '60–70% (4–5 баллов)', 'fund_help': '60–70%', 'sabo_discount': '15%', 'patient_payment': '15–25%'}
        elif score >= 2:
            return {'category': '50–60% (2–3 балла)', 'fund_help': '50–60%', 'sabo_discount': '10%', 'patient_payment': '30–40%'}
        return {'category': 'Не соответствует (0–1 балл)', 'fund_help': 'Не предоставляется', 'sabo_discount': '0%', 'patient_payment': '100% (пациент сам)'}

    income_pts = _calculate_income_points(data.get('q18_avg_income', ''))
    children_pts = _calculate_children_points(data.get('q19_children_count', ''))
    work_pts = _calculate_work_points(data.get('q21_family_work', ''))
    house_pts = _calculate_housing_points(data.get('q22_housing_type', ''))
    treatment_pts = 0
    # _calculate_treatment_importance_points(data.get('doctor_treatment_comment', ''))
    mahalla_pts = _calculate_mahalla_points(data.get('q17_need_confirmation', ''))

    total_score = income_pts + children_pts + work_pts + house_pts + treatment_pts + mahalla_pts
    support = determine_support_level(total_score)

    return {
        'patient_name': data.get('q1_full_name', '—'),
        'total_score': total_score,
        'score_max': 10,
        'score_breakdown': {
            'income': income_pts,
            'children': children_pts,
            'work': work_pts,
            'housing': house_pts,
            'treatment_importance': treatment_pts,
            'mahalla': mahalla_pts,
        },
        'support_level': support
    }


def format_conclusion_message(conclusion: dict) -> str:
    date = datetime.now().strftime("%d.%m.%Y")
    b = conclusion['score_breakdown']
    return f"""
        🏥 <b>ФИНАЛЬНОЕ ЗАКЛЮЧЕНИЕ</b>

        👤 <b>Пациент:</b> {conclusion['patient_name']}
        📅 <b>Дата:</b> {date}

        ━━━━━━━━━━━━━━━━━━━━━━━

        <b>🧮 Финансовый анализ</b>
        • Суммарный балл: <b>{conclusion['total_score']} / {conclusion['score_max']}</b>

        <b>📊 Разбивка:</b>
        • Доход: {b['income']} балл(а)
        • Дети: {b['children']} балл(а)
        • Работа: {b['work']} балл(а)
        • Жильё: {b['housing']} балл(а)
        • Важность лечения: {b['treatment_importance']} балл(а)
        • Подтверждение махалли: {b['mahalla']} балл(а)

        ━━━━━━━━━━━━━━━━━━━━━━━

        <b>🎯 Предложенный уровень поддержки:</b>
        • Категория: <b>{conclusion['support_level']['category']}</b>
        • Помощь фонда: {conclusion['support_level']['fund_help']}
        • Скидка Сабо Дармон: {conclusion['support_level']['sabo_discount']}
        • Оплата пациентом: {conclusion['support_level']['patient_payment']}

        📌 <i>Заявка будет передана комиссии. Ответ в течение 3-5 рабочих дней.</i>
        """.strip()

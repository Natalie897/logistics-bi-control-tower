# Постановки на разработку

## TASK-01: Подготовить DWH
**Вход:** `customers.csv`, `orders.csv`, `order_items.csv`. **Выход:** 4 таблицы star schema.
**Definition of Done:** все ключи валидны; 1 заказ = 1 факт; NULL SLA только при отменах; тесты зелёные.

## TASK-02: Реализовать отчёт Delivery SLA
**Вход:** `fact_orders`, `dim_date`, `dim_region`, `dim_service`.
**Выход:** страница Power BI с картами и матрицей. **DoD:** совпадает с SQL Q1–Q5 и UAT-01–05.

## TASK-03: Настроить QA и UAT
**Вход:** SQL Q7, `excel/SLA_Audit.xlsx`. **Выход:** протокол приёмки.
**DoD:** обнаруживает отрицательные значения, несоответствия FK и дубли заказов; готов чек-лист.

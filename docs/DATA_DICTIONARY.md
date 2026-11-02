# Data Dictionary

| Таблица | Поле | Тип | Правило |
|---|---|---|---|
| fact_orders | order_id | text | PK, один заказ = одна запись |
| fact_orders | order_date_key | integer | FK → dim_date |
| fact_orders | region_key | integer | FK → dim_region по штату заказчика |
| fact_orders | service_key | integer | FK → dim_service |
| fact_orders | status | text | `delivered` или `canceled` |
| fact_orders | merchandise_value | numeric | SUM(unit_price × quantity) по заказу |
| fact_orders | freight_value | numeric | Стоимость доставки, выставленная покупателю |
| fact_orders | order_value | numeric | merchandise_value + freight_value |
| fact_orders | delay_days | integer/NULL | actual_delivery − promised_delivery, NULL у отмен |
| fact_orders | is_late | 0/1/NULL | 1 если доставлен позже обещанной даты, иначе 0; NULL у отмен |
| dim_date | date_key | integer | YYYYMMDD, уникальный календарный ключ |
| dim_date | year_month | text | YYYY-MM месяц ПОКУПКИ |
| dim_region | state | text | Код региона получателя |
| dim_region | macro_region | text | Макрорегион (учебный справочник) |
| dim_service | service_type | text | economy/standard/express (синтетический источник); Olist: `not_provided` |

## Методологические определения

- **On Time Rate (%)** = доставленные вовремя / все доставленные × 100. Отменённые исключены.
- **Cancellation Rate (%)** = отменённые / все заказы × 100.
- **Gross Order Value** = сумма товаров + доставка, включая отменённые заказы. Это объём созданных заказов, **не** бухгалтерская выручка и не прибыль.
- **Late Orders** = COUNT(delivered AND actual_date > promised_date).
- **Unique Customers** = DISTINCTCOUNT(customer_id); идентификаторы Olist customer_id не равны customer_unique_id (повторные покупки могут быть недооценены).

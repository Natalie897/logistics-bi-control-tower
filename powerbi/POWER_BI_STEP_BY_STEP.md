# Power BI Desktop — точная инструкция сборки .pbix

**Важное ограничение:** отчёт Power BI Desktop (.pbix) не входит в архив, так как закрытый бинарный формат требует запуска Power BI Desktop. Здесь подготовлены четыре CSV, DAX-меры и точная модель для ручной сборки. После выполнения этой инструкции сохраните `Logistics_Control_Tower.pbix` — это и будет реальный практический навык.

## Подготовка
1. Откройте Power BI Desktop на Windows.
2. `Home / Get data / Text/CSV` и импортируйте четыре файла из `data/powerbi/`.
3. Называйте таблицы **строго** `fact_orders`, `dim_date`, `dim_region`, `dim_service`.
4. В `Transform data` установите типы: `dim_date.calendar_date` = Date; `fact_orders.promised_date`, `fact_orders.delivered_date` = Date; `*_key` = Whole Number; `is_late` = Whole Number; суммы = Decimal Number. `dim_date.year_month` = Text.
5. Проверьте отсутствие ошибок загрузки и нажмите `Close & Apply`.

## Модель данных (Model view)
- `dim_date[date_key]` (1) → `fact_orders[order_date_key]` (*);
- `dim_region[region_key]` (1) → `fact_orders[region_key]` (*);
- `dim_service[service_key]` (1) → `fact_orders[service_key]` (*).

Все связи активные, направление фильтрации **Single** (от измерений к факту). НЕ соединяйте факт с фактом. Откройте `Table tools > Mark as date table` для `dim_date`, выберите `calendar_date` (непрерывный календарь).

## DAX
Скопируйте по одному выражению из `MEASURES.dax` через `Modeling > New measure`.
Форматируйте `On Time Rate`, `Cancellation Rate`, `MoM Gross Value %` как Percentage (2 знака), суммы — как число/валюту по вашему выбору. **В учебных синтетических данных денежная единица условная.** В Olist она BRL.

## Страница 1: Executive Summary
- Карточки: `Total Orders`, `Delivered Orders`, `On Time Rate`, `Cancellation Rate`, `Gross Order Value`.
- Линейный график X = `dim_date[year_month]`, Y = `On Time Rate`.
- Столбцы X = `dim_region[macro_region]`, Y = `Late Orders`.
- Slicer: `dim_date[year_month]`, `dim_region[macro_region]`.

## Страница 2: Delivery SLA
- Bar X = `dim_service[service_type]`, Y = `On Time Rate`.
- Matrix Rows = `dim_region[state]`, Columns = `dim_service[service_type]`, Values = `On Time Rate`.
- Cards: `Avg Delivery Days`, `Average Late Days`.
- Установите условное форматирование матрицы по `%` своевременных доставок.

## Страница 3: Customer & Value
- Column chart X = `dim_date[year_month]`, Y = `Gross Order Value`.
- Cards: `Unique Customers`, `Average Order Value`, `MoM Gross Value %`.
- Bar X = `dim_region[macro_region]`, Y = `Gross Order Value`.

## Проверка
Сверьте с `excel/SLA_Audit.xlsx`, `sql/analytics_sqlite.sql` и `docs/ACCEPTANCE_CRITERIA.md`.
Для нефильтрованного демо показателя `Total Orders` ожидается 3600.
Проверки: отменённые заказы **не** входят в знаменатель своевременных доставок; `Gross Order Value` включает товары + плату за доставку; это НЕ прибыль и НЕ подтверждённая выручка.

## Сохранение
`File > Save As > Logistics_Control_Tower.pbix`.
Добавьте его в `powerbi/`, а на GitHub — скриншоты и список своих выводов. При желании сохраните также `File > Save as > Power BI Project (.pbip)` для удобных diff в Git. См. https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview

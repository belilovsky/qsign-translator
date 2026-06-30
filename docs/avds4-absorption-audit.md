# AV DS 4 Absorption Audit for QSign

## Зачем этот документ

После третьего прохода по `qsign.qdev.run` стало видно, что часть UI уже
нормально ложится на существующие блоки AV DS 4, а часть примитивов родилась
из живого продукта и может усилить общую систему. Этот документ разделяет:

1. что уже закрыто текущим AV DS 4;
2. что реально стоит вынести в `packages/ui-kit`;
3. что пока слишком доменно и должно остаться локально в QSign.

Главный принцип: в AV DS уезжает только то, что можно честно переиспользовать
в других продуктах экосистемы без тащения сурдопереводческой логики внутрь
дизайн-системы.

---

## 1. Что уже хорошо покрыто AV DS 4

Эти вещи не требуют нового компонента, максимум — маленького расширения API
или новых showcase-примеров.

### 1.1 MiniMetric

В QSign локально появился `renderMiniMetricGrid()`, но по сути это тонкий
runtime-адаптер вокруг уже существующего `MiniMetric`.

Что уже есть в AV DS:
- компактный метрика-блок;
- label/value/subtext;
- delta;
- цветовой акцент.

Что QSign добавил поверх:
- маленький kicker сверху (`словарь`, `fallback`, `проверка`, `объем`);
- дешёвый статический grid из 3–4 метрик без React-уровня композиции.

Вывод:
- **новый компонент не нужен**;
- стоит **расширить `MiniMetric` необязательным `eyebrow`/`kicker` prop**;
- отдельно стоит сделать showcase-сценарий `metric strip for quality / coverage`.

### 1.2 ScoreBar

Локальная `confidence-line` по смыслу уже совпадает с `ScoreBar`.

Что уже есть в AV DS:
- value/max;
- label;
- showValue;
- цвет по функции;
- анимация.

Что не хватает для полного совпадения:
- более явного режима для **quality/confidence semantics**;
- готовых tonal presets для `good / warn / bad`.

Вывод:
- **не новый компонент**;
- стоит добавить в `ScoreBar` **semantic preset examples** и, возможно,
  `tone="quality"` или утилиту `getQualityColor`.

### 1.3 SourceCard / SourceHealthBadge / SourcePolicyBadge

Карточки источников на QSign уже напрямую повторяют направление AV DS.

Что уже есть в AV DS:
- `SourceCard`;
- `SourceHealthBadge`;
- `SourcePolicyBadge`;
- `SourceBadge`.

Что QSign показал полезного:
- рабочий пример для каталога источников без таблицы;
- мета-ячейки `Тип / Языки / Статус`;
- длинные policy-note тексты;
- поведение при большой плотности карточек.

Вывод:
- **компонент уже в системе**;
- нужно не выносить новый, а **доработать `SourceCard`**:
  - добавить более универсальный `metaItems` API;
  - проверить режим с длинными note/policy значениями;
  - добавить showcase для registry/catalog use case.

### 1.4 ProvenanceCard

QSign подтвердил, что `ProvenanceCard` — не декоративный блок, а реально
полезный operational pattern.

Что уже есть в AV DS:
- title/summary;
- status;
- items;
- policy badge.

Чего не хватает по сравнению с боевым использованием:
- статус `draft`;
- статус `idle`;
- двухстрочный row, где есть `value + note`, а не только `value + source`;
- более “операционный” сценарий, а не только fact provenance.

Вывод:
- **компонент уже нужен системе**;
- стоит его **расширить**, а не делать параллельный новый блок.

### 1.5 BarChart

Локальный `review-language-chart` — это упрощённый operational use case для
`BarChart`.

Что уже есть в AV DS:
- простая столбчатая диаграмма;
- значения и подписи;
- hover tooltip.

Что показал QSign:
- для dashboard-плотности иногда нужен не обычный chart, а
  **row-based horizontal mini bars** для status breakdown.

Вывод:
- сам `BarChart` оставляем;
- но нужен **родственный компактный horizontal breakdown variant**.

---

## 2. Что реально стоит вынести в AV DS 4

Ниже shortlist компонентов/паттернов, которые выглядят достаточно общими.

### 2.1 WorkflowSteps

Локальный источник:
- `.stepper`, `.step`, `.step-index`
- `renderSteps(activeIndex)`

Почему это стоит унести:
- это не сурдопереводческий UI, а универсальный pattern для:
  - ingestion pipelines,
  - onboarding,
  - staged review flows,
  - publish workflows,
  - quality checks,
  - backoffice “как это работает”.

Чего сейчас нет в AV DS:
- спокойного, компактного, non-marketing step list для dashboards/tools.

Что должно быть в системной версии:
- `title`;
- `description`;
- `status`: `idle | active | done | blocked`;
- вертикальный и компактный режимы;
- optional `indexLabel`;
- responsive collapse.

Вердикт:
- **да, кандидат на новый компонент**.

### 2.2 TraceList / DecisionTrace

Локальный источник:
- `.trace-summary`
- `.trace-list`
- `.trace-step`
- `renderTrace()`

Почему это важно:
- это редкий, но очень сильный паттерн для explainability в продуктах QDev;
- подходит не только QSign, но и любым продуктам с пайплайнами:
  - fact checking,
  - generation pipelines,
  - ETL status,
  - moderation/review chains,
  - analyst workflows.

Почему не надо тащить как есть:
- тексты и статусы пока завязаны на QSign-логику (`review`, `output`, etc.).

Что стоит вынести:
- **generic `DecisionTrace`**:
  - summary metrics slot;
  - list of stages;
  - stage tone/status;
  - title + short summary per stage;
  - compact operational density.

Вердикт:
- **сильный кандидат на новый AV DS block**.

### 2.3 InspectorPanel / RecordInspector

Локальный источник:
- `.unit-inspector`
- `.unit-inspector-grid`
- `.unit-inspector-item`
- `.unit-inspector-note`

Почему это reusable:
- pattern “selected item -> compact inspector with 2–6 fields + note” нужен
  почти в каждом tool/dashboard продукте;
- это лучше, чем каждый раз вручную собирать detail card.

Что должно быть в AV DS:
- title;
- key/value fields;
- optional notes;
- compact and comfortable spacing;
- support for mono/value emphasis.

Что не надо тащить:
- доменные названия `Глосса`, `Источник`, `Оценка`.

Вердикт:
- **да, кандидат на новый primitive/block**.

### 2.4 HorizontalBreakdownBars

Локальный источник:
- `.review-language-chart`
- `.review-language-row`
- `.review-language-track`
- `.review-language-fill`

Почему это полезно:
- обычный `BarChart` не всегда подходит для плотных ops-панелей;
- row-based bar breakdown лучше работает для:
  - языков,
  - очередей,
  - источников,
  - quality categories,
  - support statuses.

Что делать:
- не плодить второй “chart framework”;
- сделать **AV DS subcomponent / variant**:
  - `BreakdownBars`
  - label + track + value
  - vertical stack
  - compact dashboard-friendly density.

Вердикт:
- **да, кандидат на новый chart-adjacent primitive**.

### 2.5 EmptyState for operational panels

Локальный источник:
- `.review-empty-state`
- его повторное использование в queue/details/feedback/audit/lexicon sections.

Почему это стоит вынести:
- сейчас у AV DS есть `LoadingSkeleton`, но нет явно выделенного
  спокойного **empty state for work surfaces**;
- повторяется почти в каждом internal tool.

Что должно быть:
- title;
- body;
- optional action slot;
- neutral, non-marketing, low-noise style.

Вердикт:
- **нужен как системный primitive**.

---

## 3. Что пока НЕ стоит забирать в AV DS

### 3.1 UnitCard / PlanCard

Локальный источник:
- `.unit-card`
- `.unit-kind`
- `.unit-gloss`
- `.unit-decision`
- `.unit-review`

Почему пока нет:
- слишком доменно завязан на sign-planning;
- смешивает selection, semantics, fallback tone, reviewer hints;
- сначала надо доказать reuse ещё хотя бы в 1–2 продуктах.

Вердикт:
- **оставить локально**.

### 3.2 TrustCard / RiskCard / WarningCard

Локальный источник:
- `.trust-card`
- `.risk-card`
- `.warning-card`

Почему осторожно:
- формально это похоже на alert/notice компоненты;
- но сейчас copy, semantics и поведение жёстко зашиты под safety claims QSign.

Что можно сделать позже:
- на уровне AV DS лучше думать не “про trust-card”, а про
  **Notice / Advisory / RiskNotice family**.

Вердикт:
- **не выносить в текущем виде**.

### 3.3 RenderPlan chips / AI brief export panel

Локальный источник:
- `.render-plan-card`
- `.render-plan-list`
- export modes и output panel.

Почему рано:
- это уже бизнес-логика конкретного AI/video workflow;
- в системе можно потом забрать только атомы, но не весь блок.

Вердикт:
- **локально**.

### 3.4 Review-specific shells

Локальный источник:
- review queue
- review detail
- review lexicon candidate cards
- review audit cards

Почему нет:
- это ближе к admin-product templates, чем к design-system primitives;
- иначе AV DS превратится в полупродуктовую библиотеку.

Вердикт:
- **не переносить**.

---

## 4. Shortlist для следующего safe batch в AV DS

Если делать маленькими шагами и без расползания scope, приоритет я вижу так:

### Batch A — быстрые доработки существующих компонентов

1. `MiniMetric`
   - добавить `kicker?: string`;
   - показать compact metric strip в showcase.

2. `ProvenanceCard`
   - расширить статус-модель: `idle | draft | verified | needs_review | stale`;
   - поддержать вторую строку note/subtext в item.

3. `SourceCard`
   - добавить `metaItems` вместо жёстко заданного PII/items/updated/attribution;
   - проверить длинные badge/note states.

4. `ScoreBar`
   - дать semantic examples для confidence/quality.

### Batch B — новые reusable blocks

1. `WorkflowSteps`
2. `DecisionTrace`
3. `InspectorPanel`
4. `EmptyState`
5. `BreakdownBars`

---

## 5. Итоговая рекомендация

Если коротко:

- **не надо** переносить в AV DS весь QSign UI кусками;
- **надо** забрать обратно только те паттерны, которые уже доказали
  операционную полезность и не привязаны к сурдопереводу как домену;
- лучший следующий шаг — **один batch на расширение существующих
  `MiniMetric / ProvenanceCard / SourceCard / ScoreBar`**, а уже потом —
  новый комплект `WorkflowSteps + DecisionTrace + InspectorPanel + EmptyState`.

Это даст AV DS 4 не “ещё один набор красивых карточек”, а действительно более
сильный toolkit для редакционных, аналитических, review и pipeline-oriented
продуктов экосистемы.

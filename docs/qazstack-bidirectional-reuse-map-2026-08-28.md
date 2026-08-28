# QSign ↔ QazStack / QDev: двусторонняя карта переиспользования

**Снимок:** 2026-08-28T18:41:01Z
**Тип результата:** внутренняя карта решений, не план миграции.
**Граница работы:** этот документ не меняет код, реестры, пакеты, CI или production.

## Короткий вывод

QSign уже является **документированным consumer** двух QazStack-прimitives:
`governance-and-audit` и `observability-and-ui`. Это подтверждено исходным
consumer contract и актуальным зеркалом Platform, но это **не** означает
установленный пакет, runtime-adoption, QazLake data plane или публичное
production-доказательство.

В ближайшей интеграционной волне есть четыре осмысленные направления:

1. сохранить contract-only потребление governance/audit и observability/UI;
2. адаптировать в QSign только общий контракт language routing и source
   normalization, не перенося sign-language-правила;
3. при появлении утверждённой модели данных связать, а не копировать,
   reviewed-activity и asset-evidence;
4. оставить compute/inference, shared identity и любые media/video operations
   в `defer` до отдельного privacy, licensing и human-review решения.

Ни одна часть QSign сейчас не проходит порог `extract_shared`: нет второго
реального совместимого consumer либо мандата Platform. Sign-plan, дактильный
fallback, лексика и финальное human review остаются специализацией QSign.

## Источники и состояние на момент сверки

| Линия | Подтверждение | Статус |
| --- | --- | --- |
| QSign source | `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator`, `main`, `ba5c6de84b9735afcb0f316259154dec92611a9f`, рабочее дерево чистое | подтверждено |
| Platform registry | `/Users/belilovsky/Documents/ChatGPT/AVPlatform/platform-portal`, `codex/platform-public-evidence-gateway-20260828`, `82f7c0c7ee177398f417fb81478c3b9cd307099f`, рабочее дерево чистое | подтверждено |
| Официальный inventory | `catalog/inventory/inventory.generated.json`, создан `2026-08-28T18:19:59Z`: **106** проектов, **37** QazStack primitives | подтверждено |
| Двусторонний contract gate | `PLATFORM_ROOT=…/platform-portal make check-platform` → `platform-contract: bilateral check passed` | source/registry proof |
| Локальный API suite | `PYTHONPATH=src python3 -m unittest tests.test_api` → 46 tests, OK | local proof |
| Публичная поверхность | `health/live` → 200; `.well-known/release.json` → 404; `.well-known/qazstack-consumer.json` → 404; `health/ready` → 503 | нет public/runtime adoption proof |

Исходный `qazstack-consumer.json` фиксирует `integration_mode:
documented-only`, `qazstack_version: contract-only` и прямо запрещает
сертифицированную интерпретацию, public review data, direct QazLake access и
browser private-media access. Эти ограничения сильнее любой рекомендации ниже.

## Правило статусов

| Статус | Значение в этой карте |
| --- | --- |
| `reuse_direct` | готовый нейтральный контракт можно принять без продуктовой семантики; сейчас таких новых переносов нет |
| `consume_shared` | QSign потребляет существующий shared contract; для текущей пары это только documentation-level, не runtime |
| `adapt_in_target` | общий контракт допустим, но язык, данные и human-review остаются в QSign |
| `link_or_federate` | связывать evidence/metadata по идентификаторам; не копировать private records или media |
| `retain_specialization` | оставить в QSign как доменную функцию |
| `extract_shared` | выделить новый QazStack primitive; требует второго реального consumer или мандата Platform |
| `defer` | хотя бы один из owner, compatibility, lifecycle, privacy или rights gate не доказан |
| `reject` | не подходит текущему QSign scope; не является оценкой качества primitive |

## Покрытие 11 обязательных плоскостей

| Плоскость | QSign-граница | Решение |
| --- | --- | --- |
| 1. Product / user | Прозрачный RU/KZ/EN draft plan, не certified interpretation; review обязателен | `retain_specialization` |
| 2. IA / access | Публичное чтение отдельно от token/cookie review surface | `defer` shared identity до roles/data minimization |
| 3. Content / localisation | Language selection можно стандартизировать; gloss, transliteration и sign semantics нельзя | `adapt_in_target` |
| 4. Data / provenance | source registry, plan units и evidence нужны; raw jobs, notes, sessions, uploads закрыты | `link_or_federate` only metadata |
| 5. UX / AVDS | QSign использует AVDS/QazStack vocabulary как presentation boundary | `consume_shared` contract-only |
| 6. Frontend | Static HTML/CSS/JS shell не даёт основания переносить чужой UI package | `reject` direct UI transfer |
| 7. Backend / API | FastAPI adapter layer; no QazLake or browser-private-media access | `defer` runtime integrations |
| 8. Platform / QazStack | Две declaration-level primitives сверены bilateral gate | `consume_shared` contract-only |
| 9. Discovery | Public context безопасен только без jobs, review, uploads, tokens, sessions и private media | `retain_specialization` |
| 10. Security / privacy / rights | Review tokens, sessions, reviewer records, raw signer/video media и license-uncertain assets не переиспользуются | `defer` / `reject` transfer |
| 11. Operations / lifecycle | QSign alpha; local proof есть, public readiness/consumer projection отсутствуют | `defer` any runtime claim |

## Доноры → QSign: решения по релевантным capability families

Владелец shared contract в таблице -- QazStack/qdev на уровне portfolio. У
самих primitive-записей owner не заполнен, поэтому это не подменяет назначение
конкретного технического owner для будущей реализации.

| Донор и contract | Данные и приватная граница | Совместимость и доказательства | Решение сейчас | Безопасный следующий шаг |
| --- | --- | --- | --- | --- |
| `governance-and-audit` (documented, 30 consumers, включая QSign) | Только policy/provenance vocabulary; без review tokens, notes и reviewer identities | QSign contract и Platform mirror совпадают; bilateral gate проходит | `consume_shared` -- **только contract-only** | При отдельной реализации назначить owner и versioned event schema; не объявлять runtime до release evidence |
| `observability-and-ui` (runtime_ready, 28 consumers, включая QSign) | Public-safe status/provenance panels; private queue и media остаются QSign-private | `avds-ui-contract.json` прямо ограничивает связь presentation vocabulary; UI stacks различаются | `consume_shared` -- **только contract-only** | Сначала принять один versioned component/state contract и accessibility acceptance; не переносить QSign review UI в shared package |
| `language-routing` (documented, 4 consumers) | Только locale/routing metadata; RU/RSL, KK/KRSL, EN/ASL lexicon и transliteration -- QSign-owned | QSign уже имеет deterministic language routing; contract-version и fallback semantics ещё не сопоставлены | `adapt_in_target`, implementation `defer` | Сравнить locale matrix и tests для ambiguous/mixed text; закрепить QSign fallback как adapter rule |
| `source-normalization` (documented, 11 consumers) | Source IDs, URLs, provenance и license-state допустимы; datasets, weights, raw clips и terms -- нет | QSign source registry содержит `needs-license-check`/`needs-code-check` записи | `adapt_in_target`, implementation `defer` | Сначала создать mapping только metadata fields и провести rights check для каждого source; не импортировать assets |
| `reviewed-activity-evidence` (runtime_ready, 4 consumers) | Допустимы immutable public-safe activity references; sessions, notes, role assignments и job bodies исключены | QSign audit exists locally, но identity model и retention contract не согласованы | `link_or_federate`, implementation `defer` | Совместно определить минимальный event envelope без PII и отдельный retention/withdrawal review |
| `asset-evidence-contracts` (documented, 4 consumers) | Asset ID, rights status, source, derivative relation; не raw signer video, face/likeness data, uploaded review MP4 | QSign media and source licenses требуют отдельной проверки | `link_or_federate`, implementation `defer` | Начать с non-media source manifest и rights-state enum; raw media сохранить за QSign boundary |
| `compute-and-inference` (runtime_ready, 9 consumers; также QazCompute) | Только bounded request metadata и reviewed draft; не private media, biometrics, unsupported weights или automated final output | ASR/video layers в QSign intentionally replaceable; model/dataset licenses не закрыты | `defer` | Отдельно утвердить model card, data processing, cost/latency envelope и mandatory human-review gate |
| `revocable-access-grants` / `id-qdev-run` (runtime_ready, 1 consumer) | Role/subject references потенциально чувствительны; QSign bootstrap token и cookie session не переносятся | Нет согласованного reviewer role mapping, issuer, retention и revoke flow | `defer` | Провести identity/privacy design review; не федерализовать текущий token/session mechanism |
| `rights-clearance` (runtime_ready, 1 consumer) | Состояние rights допустимо; лицензии datasets/weights/video нужно проверять первично | В QSign зафиксированы открытые licensing questions | `defer` | Закрыть source-by-source license decision и provenance before any connector |

### Полный охват 37 QazStack primitives

Все 37 primitive records из актуального registry были классифицированы на
уровне contract/inventory. Девять релевантных families разобраны выше.
Оставшиеся 28 имеют `reject` **для текущего QSign scope**, потому что не
показывают совместимой необходимости без расширения продукта:

`core-foundation`, `auth-and-admin`, `content-api`, `entity-store`,
`analytics-and-kznlp`, `monitoring-pipeline`, `proxy-and-transport`,
`reports-and-export`, `geo-and-location`, `editorial-runtime`,
`temporal-contracts`, `factcheck-evidence`, `telegram-alerting`,
`collectors-and-entity-pipeline`, `media-search-and-dedup`,
`finance-and-market-data`, `disclosure-group`, `ranked-search`,
`pagination-and-listing`, `tasking-and-resilience`, `databus-and-bus`,
`document-ocr`, `communications-operations`, `opportunity-contracts`,
`agent-interfaces-and-mcp`, `process-models-and-workflows`,
`thematic-product-contracts`, `open-kitchen`.

Это исключает, в частности, перенос collector/data-bus, finance, OCR,
messaging и generic workflow surface в sign-language prototype без
подтверждённой пользовательской потребности и privacy contract.

## Экран 106 продуктов Platform

Сверка выполнена по всем 106 записям официального inventory, а не по похожим
локальным checkout. Для глубокой contract-сверки выделены только потенциальные
доноры; остальные не дают доказанного reusable capability в metadata и остаются
`reject` для данной карты, а не «непроверенными переносами».

| Потенциальный донор | Почему рассмотрен | Итог |
| --- | --- | --- |
| `qazstack` | владелец 37 общих primitives | единственный путь shared contracts; см. таблицу выше |
| `av-platform-core` | AVDS presentation/accessibility contracts | `consume_shared` only as existing QSign boundary; no review-UI extraction |
| `qazcompute` | production compute platform | `defer`: model/data/privacy/human-review gates отсутствуют |
| `id-qdev-run` | shared identity service | `defer`: current QSign token/cookie sessions не являются federated access contract |
| `qazread` | runtime consumer reviewed-activity evidence | `link_or_federate` candidate only; не второй consumer QSign semantics |
| `qradio` | language/audio adjacent service | `reject` direct transfer; possible future comparative input only |
| `photo-finder` / QPhoto | asset/provenance-adjacent service | `link_or_federate` metadata candidate only; no signer/video media transfer |

Ни один из этих продуктов не засчитывается как второй реальный consumer
QSign-specialization. Для этого нужны обоюдно утверждённый contract, owner,
lifecycle и реальные adoption evidence.

## QSign → портфель: обратные решения

| Актив QSign | Owner и приватная граница | Решение | Почему | Безопасный следующий шаг |
| --- | --- | --- | --- | --- |
| Sign-plan units, confidence и ordering | QSign/qdev; domain semantics and possibly user input | `retain_specialization` | Это ядро sign-language draft planning, не domain-neutral primitive | Сохранить versioned local schema; публиковать только public-safe methodology |
| Дактильный fallback | QSign/qdev; зависит от RU/KZ/EN-to-sign-language rules | `retain_specialization` | OOV policy, visible fallback and no-silent-hallucination rule специфичны QSign | Описать как product policy, не переносить в generic language-routing |
| Human review state, review session и final publish decision | QSign/qdev; tokens, sessions, reviewer identity, notes and private media excluded | `link_or_federate` | Общим может стать только minimal evidence envelope; workflow и data остаются локальными | После privacy review сопоставить с `reviewed-activity-evidence`; не extract shared |
| Source registry policy | QSign/qdev; dataset/weight/clip rights stay source-specific | `link_or_federate` | Общи source IDs/right-status fields, но research eligibility и licensing decisions не generic | После license closure mapping to `source-normalization` / `rights-clearance` |
| AI video brief and render plan | QSign/qdev; private media, likeness and model provenance sensitive | `defer` | Нет второго реального consumer, stable media contract или rights proof | Не извлекать; лишь после two-consumer evidence + Platform mandate assess `asset-evidence-contracts` extension |
| AVDS review/provenance presentation patterns | QSign + AVDS boundary; never expose review internals | `link_or_federate` | Presentation patterns already point to AVDS/QazStack vocabulary; underlying review semantics local | Continue component-level AVDS acceptance, without exporting QSign-specific cards |
| Public methodology and safe discovery descriptions | QSign/qdev; excludes jobs, review, uploads, tokens, sessions and private media | `retain_specialization` | Claims, languages and human-review limits are product-specific | Reuse only as cited public documentation, not a shared API contract |

**Новый shared module:** отсутствует. Возможные соседние интересы QazRead,
QRadio и QPhoto не являются вторым consumer until a real, approved integration
exists. Поэтому `extract_shared = 0`.

## Стоп-факторы и порядок следующего отдельного этапа

1. Не выдавать локальные source/registry доказательства за runtime или public
   proof: production consumer projection и release JSON сейчас возвращают 404,
   readiness -- 503.
2. Не переносить review tokens, cookie sessions, review data, raw signer/video
   media, uploads, biometric/likeness data, dataset copies, model weights или
   source material с незакрытой лицензией.
3. Для любого `defer` сначала получить конкретный owner, versioned contract,
   compatibility tests, privacy/rights decision и rollback path.
4. `extract_shared` разрешать только после второго реального совместимого
   consumer либо прямого мандата Platform; до этого сохранять QSign local.

Если карта будет утверждена, следующий этап должен быть отдельной задачей:
один выбранный contract, один owner, ограниченный adapter в QSign, локальные
tests и затем независимые runtime/public evidence. Эта карта сама по себе
ничего не публикует и не меняет.

## Проверка документа

- Source SHA, Platform SHA, чистота деревьев и inventory count зафиксированы
  выше до принятия решений.
- QSign consumer contract сверялся с `qdev-project.json`,
  `avds-ui-contract.json`, public discovery documents и Platform primitive
  registry bilateral gate.
- Статусы разделяют source, local-test, registry и public/runtime evidence.
- Неизвестные owner, license, privacy boundary, versioned compatibility или
  второй consumer оставлены в `defer`; ни один не превращён в implementation
  claim.

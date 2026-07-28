# NEXUS Memory: Hafıza Denetimi ve Geçiş Hazırlığı (Phase 0.5)

> **Sürüm:** 1.0.0
> **Statü:** Hazır
> **Tarih:** Temmuz 2026
> **Yazar:** Jules (Principal Systems Architect)

---

## 1. Giriş ve Amaç

NEXUS Memory mimarisinin 1. Aşamasına geçmeden önce, mevcut sistemde (Elite Decision Engine) birikmiş olan kurumsal/operasyonel verilerin tam bir denetimini (Memory Audit) yapmak ve bu verileri **Layer 0 (L0) Değişmez Olay Günlüğü** formatına dönüştürecek geçiş hazırlıklarını tamamlamak kritik öneme sahiptir.

Bu doküman, sistemdeki mevcut veritabanı tablolarının envanterini, veri kalitesi analizini, nedensel köken (provenance) kurallarını, L0 Canonical Event Schema eşlemelerini ve veri temizleme (cleansing) stratejilerini detaylandırmaktadır. Amaç, hiçbir veri veya tecrübe kaybı yaşamadan tam bir kurumsal hafıza aktarımı sağlamaktır.

---

## 2. Mevcut Veri Kaynakları Envanteri (Data Inventory)

Sistemdeki mevcut ilişkisel tablolar, bunların kaliteleri, içerdikleri köken (provenance) bilgileri ve göç öncelikleri aşağıda listelenmiştir:

| Sıra | Tablo Adı | Tanım / Rol | Önemli Alanlar & Tipleri | Veri Kalitesi & Tespit Edilen Riskler | Provenance Bağlantıları | Göç Önceliği |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | `signals` | Karar mekanizmasını tetikleyen ham sinyaller | `id` (Int), `symbol` (Str), `side` (Str), `price` (Float), `score` (Float), `status` (Str), `created_at` (DateTime) | **Yüksek Kalite.** Zaman damgaları ve puanlar her zaman mevcuttur. | Yok (Tetikleyici olay) | **Kritik (1)** |
| **2** | `decision_explanations` | Sinyale verilen kararın AI gerekçesi | `id` (Int), `signal_id` (Int), `decision` (Str), `reasons` (JSON), `summary` (Text), `created_at` (DateTime) | **Orta Kalite.** Bazı eski sinyaller için açıklama bulunmayabilir. | `signal_id` -> `signals.id` | **Kritik (2)** |
| **3** | `paper_orders` | Sinyal sonrası iletilen borsa emirleri | `id` (Int), `symbol` (Str), `side` (Str), `quantity` (Float), `filled_price` (Float), `status` (Str), `trade_id` (Int) | **Orta Kalite.** `filled_price` iptal edilen emirler için NULL olabilir. | `trade_id` -> `trades.id` | **Yüksek (3)** |
| **4** | `paper_trades` | Gerçekleşen borsa işlemleri (Trades) | `id` (Int), `position_id` (Int), `symbol` (Str), `side` (Str), `entry` (Float), `pnl` (Float), `status` (Str) | **Yüksek Kalite.** İşlem detayları tamdır. | `position_id` -> `trades.id` | **Yüksek (4)** |
| **5** | `trades` | Sistem içi takip edilen pozisyonlar | `id` (Int), `signal_id` (Int), `symbol` (Str), `entry` (Float), `stop` (Float), `pnl` (Float), `status` (Str) | **Yüksek Kalite.** `exchange_order_id` her zaman dolu olmayabilir. | `signal_id` -> `signals.id` | **Yüksek (5)** |
| **6** | `journal_entries` | Kullanıcı veya sistem günlüğü / notları | `id` (Int), `symbol` (Str), `entry_price` (Float), `notes` (Text), `result` (Str), `signal_id` (Int), `trade_id` (Int) | **Düşük Kalite.** `notes` alanı yapılandırılmamış serbest metin veya düzensiz JSON içerebilir. | `signal_id` -> `signals.id`, `trade_id` -> `trades.id` | **Orta (6)** |

---

## 3. Hedef Olay Şeması Eşlemesi (Target L0 Event Mappings)

Göç esnasında her bir legacy kayıt, **Canonical Event Schema** yapısına uygun birer olaya dönüştürülür. Eşleme kuralları şu şekildedir:

### 3.1. `signals` -> `SIGNAL_RECEIVED`
* **Event Type:** `SIGNAL_RECEIVED`
* **Actor:** `{ "id": "market_scanner", "type": "SYSTEM", "name": "Market Scanner Engine" }`
* **Provenance:**
  - `causal_chain_id`: Yeni üretilen UUID (bu zincirin başlangıcıdır).
  - `parent_event_id`: NULL.
* **Payload Eşlemesi:**
  ```json
  {
    "legacy_signal_id": signals.id,
    "symbol": signals.symbol,
    "side": signals.side,
    "price": signals.price,
    "technical_scores": {
      "volume": signals.volume_score,
      "funding": signals.funding_score,
      "oi": signals.oi_score,
      "trend": signals.trend_score,
      "risk": signals.risk_score
    },
    "market_health": {
      "overall": signals.market_health,
      "btc": signals.btc_health
    }
  }
  ```

### 3.2. `decision_explanations` -> `DECISION_EXPLANATION_GENERATED`
* **Event Type:** `DECISION_EXPLANATION_GENERATED`
* **Actor:** `{ "id": "ai_council", "type": "AGENT", "name": "NEXUS AI Council" }`
* **Provenance:**
  - `causal_chain_id`: `signals` adımında üretilen UUID.
  - `parent_event_id`: `SIGNAL_RECEIVED` olayının UUID'si.
* **Payload Eşlemesi:**
  ```json
  {
    "legacy_explanation_id": decision_explanations.id,
    "decision": decision_explanations.decision,
    "confidence": decision_explanations.confidence,
    "reasons": decision_explanations.reasons,
    "warnings": decision_explanations.warnings,
    "summary": decision_explanations.summary,
    "metrics_snapshot": {
      "technical_score": decision_explanations.technical_score,
      "whale_score": decision_explanations.whale_score,
      "risk_score": decision_explanations.risk_score
    }
  }
  ```

### 3.3. `paper_orders` -> `ORDER_CREATED` / `ORDER_CANCELLED`
* **Event Type:** `ORDER_CREATED` veya `ORDER_FILLED` (Duruma göre çoklu event üretilir)
* **Actor:** `{ "id": "order_manager", "type": "SYSTEM", "name": "Order Management System" }`
* **Provenance:**
  - `causal_chain_id`: İlgili sinyale ait UUID.
  - `parent_event_id`: Karar açıklaması olayının UUID'si.
* **Payload Eşlemesi:**
  ```json
  {
    "legacy_order_id": paper_orders.id,
    "symbol": paper_orders.symbol,
    "side": paper_orders.side,
    "order_type": paper_orders.order_type,
    "quantity": paper_orders.quantity,
    "price": paper_orders.price,
    "filled_price": paper_orders.filled_price,
    "status": paper_orders.status
  }
  ```

### 3.4. `trades` & `paper_trades` -> `TRADE_OPENED` / `TRADE_CLOSED`
* **Event Type:** `TRADE_OPENED` ve `TRADE_CLOSED` (Eğer işlem kapalı ise iki ayrı olay kronolojik sırayla oluşturulur)
* **Actor:** `{ "id": "paper_executor", "type": "SYSTEM", "name": "Paper Trading Executor" }`
* **Provenance:**
  - `causal_chain_id`: İlgili sinyale ait UUID.
  - `parent_event_id`: `ORDER_CREATED` veya bir önceki operasyonel olay UUID'si.
* **Payload Eşlemesi (`TRADE_CLOSED` için):**
  ```json
  {
    "legacy_trade_id": trades.id,
    "symbol": trades.symbol,
    "side": trades.side,
    "entry_price": trades.entry,
    "exit_price": trades.exit_price,
    "stop_loss": trades.stop,
    "take_profit_1": trades.tp1,
    "take_profit_2": trades.tp2,
    "pnl": trades.pnl,
    "close_reason": trades.close_reason,
    "closed_at": trades.closed_at
  }
  ```

---

## 4. Nedensel Köken ve Bağlama Kuralları (Linkage & Provenance Logic)

Göç motoru, ilişkisel tabloları tararken nedensellik çizgesini (Causal Graph) kurmak için aşağıdaki algoritmayı uygular:

1. **Sinyal Merkezli Gruplama:** Göç işlemi sinyal bazlı yürütülür. `signals` tablosundaki her bir kayıt için tekil bir `causal_chain_id` (UUIDv4) üretilir.
2. **Adım Adım Olay Zinciri Oluşturma:**
   - İlk olarak `SIGNAL_RECEIVED` olayı oluşturulur ve kaydedilir.
   - Sinyale bağlı bir `decision_explanation` varsa, `parent_event_id` olarak bir önceki sinyal olayının UUID'si verilir ve `DECISION_EXPLANATION_GENERATED` olayı oluşturulur.
   - Sinyale bağlı bir `trade` veya `paper_order` varsa, bunlar zincirin bir sonraki halkası olarak bağlanır.
3. **Kopuk Kayıtların Yönetimi (Dangling Records):**
   - Eğer sistemde bir `trade` veya `paper_order` kaydının bağlı olduğu sinyal veritabanından silinmişse, göç motoru bu kayıt için sanal bir `SIGNAL_RECEIVED` olayı üreterek veri bütünlüğünü ve şema zorunluluklarını korur.

---

## 5. Veri Kalitesi ve Temizleme Kuralları (Cleansing Rules)

Göç esnasında verilerin tutarlılığını sağlamak için şu temizleme ve dönüştürme kuralları uygulanır:

1. **Zaman Damgası Normalizasyonu:** Tüm zaman damgaları UTC zaman dilimine dönüştürülür ve ISO 8601 formatına (`YYYY-MM-DDTHH:MM:SS.mmmmmmZ`) getirilerek kaydedilir.
2. **Eksik Değerlerin (Nulls) Güvenli Yönetimi:**
   - Sayısal eksiklikler (Örn: `pnl` boşsa) `0.0` ile doldurulur.
   - Metinsel eksiklikler (Örn: `exit_reason` boşsa) `"UNKNOWN"` veya `"NOT_SPECIFIED"` olarak kaydedilir.
3. **Kriptografik Bütünlük (SHA-256 Checksum):**
   L0 katmanının değişmezlik (immutability) ilkesini garanti etmek için, oluşturulan her Canonical Event nesnesi için bir SHA-256 hash imzası oluşturulur. Formül:
   $$\text{Checksum} = \text{SHA256}(\text{event\_id} + \text{seq\_id} + \text{timestamp} + \text{event\_type} + \text{JSON}(payload))$$
   Bu değer her olayın `checksum` alanında saklanır.

---

## 6. Migration Engine Yazılım Mimarisi

Geliştirilecek olan `NEXUSMigrationEngine` (`memory/migration_engine.py`), modüler bir yapıya sahip olacak ve şu alt bileşenleri barındıracaktır:

* **Extractor (Veri Çekici):** SQL tabanlı ilişkisel veritabanından (PostgreSQL/SQLite) ham kayıtları çeker.
* **Transformer (Dönüştürücü):** Ham ilişkisel satırları Canonical Event şemasına dönüştürür, UUID'leri ve checksum imzalarını hesaplar.
* **Loader (Yükleyici):** Dönüştürülen olayları L0 Event Log tablosuna toplu (batch) veya işlemsel (transactional) olarak yazar.
* **Validator (Doğrulayıcı):** Yazılan olayların bütünlüğünü ve nedensel bağlarını kontrol eder.

Söz konusu motorun iskeleti bir sonraki adımda `memory/migration_engine.py` içerisinde kurulacaktır.

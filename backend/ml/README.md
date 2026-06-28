# 🧠 Machine Learning — FlowAgent AI

This submodule contains all local machine learning models used by FlowAgent AI for fast, **privacy-preserving inference** — no external API calls required.

---

## 📁 Directory Structure

```
backend/ml/
├── train_models.py    # Trains all 4 models with synthetic data; auto-run on first boot
├── predictors.py      # Inference functions for all 4 models (with rule-based fallbacks)
├── forecaster.py      # Ticket volume time-series forecaster
├── churn_model.py     # Churn model training logic
└── models/            # Saved .joblib model files (auto-generated)
    ├── sentiment_model.joblib
    ├── ticket_classifier.joblib
    ├── lead_scorer.joblib
    └── churn_model.joblib
```

---

## 🤖 Models Overview

All models are trained on **synthetically generated datasets** created in `train_models.py`. This means the system works **out of the box with no external training data** required.

| Model | File | Algorithm | Input Features | Output Classes |
|---|---|---|---|---|
| Sentiment Classifier | `sentiment_model.joblib` | TF-IDF + Logistic Regression | Customer message text | `Positive`, `Neutral`, `Negative` |
| Ticket Classifier | `ticket_classifier.joblib` | TF-IDF + LinearSVC | Customer message text | `Billing`, `Technical`, `Account`, `Refund`, `General Inquiry` |
| Lead Scorer | `lead_scorer.joblib` | Decision Tree Classifier | Numeric engagement features | `Hot`, `Warm`, `Cold` |
| Churn Predictor | `churn_model.joblib` | Random Forest Classifier | Customer health metrics | `High`, `Medium`, `Low` |

---

## 📊 Model Details

### 1. Sentiment Classifier

**Purpose**: Detects the emotional tone of a customer's message to set ticket priority and guide the Customer Care Agent's response.

**Pipeline**: `TfidfVectorizer(ngram_range=(1,2), max_features=5000)` → `LogisticRegression`

**Training Data**: ~1,500 synthetic text samples with labels: Positive / Neutral / Negative

**Priority Mapping**:
- `Negative` → Priority: **High**
- `Neutral` → Priority: **Medium**
- `Positive` → Priority: **Low**

---

### 2. Ticket Classifier

**Purpose**: Automatically categorizes support tickets into departments to route them correctly.

**Pipeline**: `TfidfVectorizer(ngram_range=(1,2))` → `LinearSVC`

**Categories**:

| Category | Example Keywords |
|---|---|
| `Billing` | invoice, payment, charge, fee, subscription |
| `Technical` | error, crash, bug, timeout, API, server |
| `Account` | password, login, locked, profile, email |
| `Refund` | refund, cancel, money back, trial charge |
| `General Inquiry` | everything else |

---

### 3. Lead Scorer

**Purpose**: Qualifies sales leads based on their engagement metrics. Used by the Sales Agent when buying intent is detected.

**Algorithm**: Decision Tree Classifier

**Input Features**:

| Feature | Description |
|---|---|
| `page_views` | Number of pages visited |
| `time_on_site` | Seconds spent on site |
| `form_submitted` | 1 if contact form was filled, else 0 |
| `email_type` | 1 if professional email domain, 0 if Gmail/Yahoo/etc. |
| `interaction_count` | Number of past interactions |

**Heuristic Score** (0–100): Used to override ML prediction at extremes:
```
score = page_views × 1.5 + time_on_site/15 + form_submitted × 30 + is_professional_email × 20 + interactions × 4
```

**Output**:
- `Hot` (score ≥ 60): High-priority lead — book a call immediately
- `Warm` (score 35–59): Nurture with follow-up content
- `Cold` (score < 35): Low engagement — add to drip campaign

---

### 4. Churn Predictor

**Purpose**: Predicts the likelihood that a customer will churn (cancel), enabling proactive retention actions.

**Algorithm**: Random Forest Classifier (100 estimators)

**Input Features**:

| Feature | Description |
|---|---|
| `negative_tickets` | Count of tickets with Negative sentiment |
| `escalations` | Count of tickets escalated to human agents |
| `days_since_last` | Days since the last ticket/interaction |
| `clv` | Customer Lifetime Value (₹) |
| `health_score` | Composite health score (0–100, higher = healthier) |

**Risk Score** (0–100):
```
risk = negative_tickets × 15 + escalations × 20 + days_since_last × 0.5 + (100 - health_score) × 0.5 - (clv / 200)
```

**Output**:
- `High` (risk ≥ 65): Immediate retention action needed
- `Medium` (risk 35–64): Monitor closely, offer incentives
- `Low` (risk < 35): Customer is healthy

---

## 📈 Forecaster (`forecaster.py`)

**Purpose**: Predicts upcoming ticket volume for operational capacity planning.

**Algorithm**: Time-series linear regression over historical daily ticket counts.

**API Endpoint**: `GET /api/analytics/forecast` *(Manager role required)*

**Output**: Projected ticket counts for the next 7 days with trend indicators.

---

## ⚡ Training the Models

### Automatic (on first boot)

When `run.py` is executed and `.joblib` files are missing, `train_all()` runs automatically:

```bash
python run.py
# → "ML Models missing. Triggering training..."
# → Trains all 4 models and saves .joblib files
```

### Manual Retraining

```bash
# Via Python
python -m backend.ml.train_models

# Via API (runs in background, non-blocking)
curl -X POST http://localhost:8000/api/train
```

---

## 🛡️ Fallback Behavior

All prediction functions in `predictors.py` include **rule-based fallbacks**. If the `.joblib` file fails to load (e.g., version mismatch, corruption), the system falls back to deterministic keyword rules:

```python
# Example: sentiment fallback
if any(w in text.lower() for w in ["love", "great", "excellent", "happy"]):
    return "Positive"
elif any(w in text.lower() for w in ["upset", "angry", "terrible", "scam"]):
    return "Negative"
return "Neutral"
```

This ensures the platform **never crashes due to ML model issues** — it degrades gracefully while still being functional.

---

## 🔁 Model Caching

Models are loaded once at startup and cached in a module-level `models` dictionary:

```python
models = {
    "sentiment": None,
    "ticket_classifier": None,
    "lead_scorer": None,
    "churn": None
}
```

Subsequent prediction calls use the in-memory cache — no disk I/O per request.

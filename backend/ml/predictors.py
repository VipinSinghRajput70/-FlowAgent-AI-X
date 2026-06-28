import os
import joblib
import pandas as pd
import numpy as np

# Setup paths
ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")

# Cache models in memory
models = {
    "sentiment": None,
    "ticket_classifier": None,
    "lead_scorer": None,
    "churn": None
}

def load_models():
    sentiment_path = os.path.join(MODELS_DIR, "sentiment_model.joblib")
    ticket_path = os.path.join(MODELS_DIR, "ticket_classifier.joblib")
    lead_path = os.path.join(MODELS_DIR, "lead_scorer.joblib")
    churn_path = os.path.join(MODELS_DIR, "churn_model.joblib")
    
    # Check if models exist, if not, print warning
    if not (os.path.exists(sentiment_path) and os.path.exists(ticket_path) and 
            os.path.exists(lead_path) and os.path.exists(churn_path)):
        print("Warning: ML models are missing. Please run train_models.py first.")
        return False
        
    try:
        models["sentiment"] = joblib.load(sentiment_path)
        models["ticket_classifier"] = joblib.load(ticket_path)
        models["lead_scorer"] = joblib.load(lead_path)
        models["churn"] = joblib.load(churn_path)
        print("ML models loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading ML models: {e}")
        return False

# Load automatically when imported
load_models()

def predict_sentiment(text: str) -> str:
    """Predicts sentiment of input text. Returns: Positive, Neutral, or Negative."""
    if not models["sentiment"]:
        # Fallback to simple rule-based if model not loaded
        text_lower = text.lower()
        if any(w in text_lower for w in ["love", "great", "excellent", "perfect", "good", "thank", "happy"]):
            return "Positive"
        elif any(w in text_lower for w in ["upset", "angry", "worst", "terrible", "crash", " refund", "broken", "useless", "scam"]):
            return "Negative"
        return "Neutral"
        
    try:
        pred = models["sentiment"].predict([text])[0]
        return str(pred)
    except Exception as e:
        print(f"Sentiment prediction error: {e}")
        return "Neutral"

def predict_ticket_category(text: str) -> str:
    """Classifies ticket into: Billing, Technical, Account, Refund, General Inquiry"""
    if not models["ticket_classifier"]:
        # Fallback rule-based
        text_lower = text.lower()
        if any(w in text_lower for w in ["charge", "invoice", "payment", "price", "billing", "fee"]):
            return "Billing"
        elif any(w in text_lower for w in ["refund", "cancel", "money back", "trial charge"]):
            return "Refund"
        elif any(w in text_lower for w in ["password", "login", "locked", "account", "profile"]):
            return "Account"
        elif any(w in text_lower for w in ["error", "crash", "timeout", "api", "server", "code", "bug"]):
            return "Technical"
        return "General Inquiry"
        
    try:
        pred = models["ticket_classifier"].predict([text])[0]
        return str(pred)
    except Exception as e:
        print(f"Ticket category classification error: {e}")
        return "General Inquiry"

def is_professional_email(email: str) -> int:
    """Returns 1 if the email is professional, 0 if it is a common public domain."""
    email = email.lower().strip()
    public_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "mail.com"]
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain or domain in public_domains:
        return 0
    return 1

def predict_lead_score(page_views: int, time_on_site: int, form_submitted: int, email: str, interaction_count: int = 1):
    """
    Predicts lead status (Hot, Warm, Cold) and computes a lead score from 0 to 100.
    """
    is_prof = is_professional_email(email)
    
    # Calculate a raw heuristic score to return as the 0-100 metric
    raw_score = (
        min(page_views, 20) * 1.5 + 
        min(time_on_site / 15.0, 30) * 1.0 + 
        form_submitted * 30.0 + 
        is_prof * 20.0 + 
        min(interaction_count, 5) * 4.0
    )
    raw_score = min(max(int(raw_score), 0), 100)
    
    if not models["lead_scorer"]:
        # Fallback rule-based status
        if raw_score >= 60:
            status = "Hot"
        elif raw_score >= 35:
            status = "Warm"
        else:
            status = "Cold"
        return status, raw_score
        
    try:
        # Features order matching training:
        # ["page_views", "time_on_site", "form_submitted", "email_type", "interaction_count"]
        features = pd.DataFrame([[page_views, time_on_site, form_submitted, is_prof, interaction_count]],
                                columns=["page_views", "time_on_site", "form_submitted", "email_type", "interaction_count"])
        status = models["lead_scorer"].predict(features)[0]
        
        # Override class mappings if they disagree wildy with raw_score
        if raw_score > 75:
            status = "Hot"
        elif raw_score < 25:
            status = "Cold"
            
        return str(status), raw_score
    except Exception as e:
        print(f"Lead scoring prediction error: {e}")
        # Rule fallback
        if raw_score >= 60:
            status = "Hot"
        elif raw_score >= 35:
            status = "Warm"
        else:
            status = "Cold"
        return status, raw_score

def predict_churn_risk(negative_tickets: int, escalations: int, days_since_last: int, clv: float, health_score: int):
    """
    Predicts churn risk status (Low, Medium, High) and risk probability.
    """
    raw_risk = (
        negative_tickets * 15 +
        escalations * 20 +
        days_since_last * 0.5 +
        (100 - health_score) * 0.5 -
        (clv / 200.0)
    )
    raw_risk = min(max(int(raw_risk), 0), 100)
    
    if not models["churn"]:
        if raw_risk >= 65:
            status = "High"
        elif raw_risk >= 35:
            status = "Medium"
        else:
            status = "Low"
        return status, raw_risk
        
    try:
        # Features order matching training:
        # ["negative_tickets", "escalations", "days_since_last", "clv", "health_score"]
        features = pd.DataFrame([[negative_tickets, escalations, days_since_last, clv, health_score]],
                                columns=["negative_tickets", "escalations", "days_since_last", "clv", "health_score"])
        status = models["churn"].predict(features)[0]
        
        # Override class mappings if they disagree wildly with raw_risk score
        if raw_risk > 75:
            status = "High"
        elif raw_risk < 25:
            status = "Low"
            
        return str(status), raw_risk
    except Exception as e:
        print(f"Churn risk prediction error: {e}")
        if raw_risk >= 65:
            status = "High"
        elif raw_risk >= 35:
            status = "Medium"
        else:
            status = "Low"
        return status, raw_risk

def simulate_scenario_metrics(staff_change: float, price_change: float, campaign_launch: bool) -> dict:
    """
    Simulates the operational and revenue impact of changing support staffing,
    pricing models, and launching new marketing campaigns.
    Returns a dictionary of predicted CSAT, queue latency, churn rate, and monthly ROI impact.
    """
    # Baselines
    base_csat = 85.0
    base_latency = 2.5 # hours
    base_churn_rate = 5.4 # %
    base_daily_revenue = 150000.0 # INR
    
    # 1. Staffing impact
    csat = base_csat
    latency = base_latency
    churn = base_churn_rate
    cost_change_daily = (staff_change / 100.0) * 10 * 2000.0 # Assumes 10 baseline agents, costing ₹2,000/day each
    
    if staff_change < 0:
        # Laying off staff increases latency and decreases CSAT
        latency = base_latency * (1.0 + abs(staff_change / 100.0) * 2.5)
        csat = base_csat - abs(staff_change / 100.0) * 18.0
        churn = base_churn_rate + abs(staff_change / 100.0) * 7.0
    elif staff_change > 0:
        # Hiring staff decreases latency, minor boost to CSAT
        latency = base_latency / (1.0 + (staff_change / 100.0) * 1.2)
        csat = base_csat + (staff_change / 100.0) * 4.0
        churn = base_churn_rate - (staff_change / 100.0) * 2.0
        
    # 2. Pricing impact
    revenue_multiplier = 1.0
    if price_change > 0:
        # Price hike increases churn, drops CSAT, increases revenue per user
        churn += (price_change / 100.0) * 11.0
        csat -= (price_change / 100.0) * 8.0
        revenue_multiplier = (1.0 + price_change / 100.0) * (1.0 - (price_change / 100.0) * 0.4)
    elif price_change < 0:
        # Price cut decreases churn, increases CSAT, decreases revenue per user
        churn -= abs(price_change / 100.0) * 5.0
        csat += abs(price_change / 100.0) * 4.0
        revenue_multiplier = (1.0 - abs(price_change / 100.0)) * (1.0 + abs(price_change / 100.0) * 0.2)
        
    # 3. Campaign launch impact
    campaign_rev_daily = 0.0
    campaign_cost_daily = 0.0
    if campaign_launch:
        # Boosts inbound load, increases revenue, decreases churn due to brand awareness
        campaign_rev_daily = 65000.0
        campaign_cost_daily = 15000.0
        latency *= 1.18
        csat += 2.0
        churn *= 0.85
        
    # Bounds checking
    csat = min(max(round(csat, 1), 20.0), 99.0)
    latency = min(max(round(latency, 2), 0.1), 48.0)
    churn = min(max(round(churn, 1), 0.5), 80.0)
    
    # Financial calculation (Monthly ROI Impact = 30 days)
    revenue_change_daily = base_daily_revenue * (revenue_multiplier - 1.0) + campaign_rev_daily
    net_daily_impact = revenue_change_daily - cost_change_daily - campaign_cost_daily
    monthly_roi_impact = int(round(net_daily_impact * 30.0))
    
    return {
        "predicted_csat": csat,
        "predicted_backlog_latency": latency,
        "predicted_churn_rate": churn,
        "predicted_roi_impact": monthly_roi_impact
    }

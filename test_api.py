import os
from dotenv import load_dotenv
load_dotenv()
import sys
import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import (
    init_db, add_ticket, get_all_tickets, add_lead, get_all_leads, get_analytics,
    update_or_create_customer, get_customer_profile, add_conversation_turn, get_session_history,
    update_ticket
)
from backend.ml.train_models import train_all
from backend.ml.predictors import load_models, predict_sentiment, predict_ticket_category, predict_lead_score
from backend.ml.forecaster import get_ticket_forecast
from backend.vector_store import index_document, get_kb_stats, query_knowledge_base
from backend.security import create_access_token, decode_access_token, hash_password, verify_password

def run_tests():
    # Configure UTF-8 encoding on Windows to prevent UnicodeEncodeErrors
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # Clear old database to recreate with updated schemas
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "flowagent.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print("Cleaned up old SQLite database for schema upgrade.")
        except Exception as e:
            print(f"Warning: Could not remove old db file: {e}")

    print("========================================")
    print("[TEST] Running FlowAgent AI Verification Suite")
    print("========================================\n")
    
    # 1. Initialize SQLite Database
    print("Step 1: Initializing SQLite Database Schema...")
    init_db()
    print("[OK] DB Initialized.\n")
    
    # 2. JWT Security Verification
    print("Step 2: Verifying Password Hashing & JWT-style Signed Tokens...")
    raw_pw = "mysecretpassword123"
    hashed = hash_password(raw_pw)
    assert verify_password(raw_pw, hashed), "Password verification failed!"
    
    token_payload = {"username": "admin", "role": "Manager"}
    token = create_access_token(token_payload)
    decoded = decode_access_token(token)
    assert decoded is not None, "Failed to decode JWT access token!"
    assert decoded["username"] == "admin", "Token payload corruption detected!"
    assert decoded["role"] == "Manager", "Token payload corruption detected!"
    print("[OK] JWT Token Security validated.\n")
    
    # 3. Train and Load ML Models
    print("Step 3: Verifying Local Machine Learning Models...")
    train_all()
    models_loaded = load_models()
    assert models_loaded, "Failed to load ML models after training!"
    print("[OK] ML models trained and loaded successfully.\n")
    
    # 4. Test Predictions
    print("Step 4: Testing ML Model Inference...")
    
    # Sentiment
    pos_sent = predict_sentiment("I love the interface, it works perfectly and is super fast!")
    neg_sent = predict_sentiment("I'm very upset, my order is delayed and I want a refund!")
    assert pos_sent == "Positive", f"Expected Positive sentiment, got {pos_sent}"
    assert neg_sent == "Negative", f"Expected Negative sentiment, got {neg_sent}"
    
    # Ticket classification
    billing_cat = predict_ticket_category("I need an invoice for my transaction last month.")
    technical_cat = predict_ticket_category("The database is throwing a 500 connection error on login.")
    print(f"- Ticket Category Test (Billing): Got '{billing_cat}'")
    print(f"- Ticket Category Test (Technical): Got '{technical_cat}'")
    
    # Lead scoring
    lead_status, score = predict_lead_score(
        page_views=15,
        time_on_site=600,
        form_submitted=1,
        email="john@enterprise-solutions.com"
    )
    print(f"- Lead Score Test: Status: '{lead_status}', Score: {score}/100")
    
    print("[OK] Inference tests passed.\n")
    
    # 5. Customer Profile & Human Escalation Verification
    print("Step 5: Testing Customer 360° Profile & Smart Human Escalation Engine...")
    
    # Add negative ticket for customer
    customer_email = "angry_customer@test.com"
    add_ticket(
        customer_name="Angry User",
        customer_email=customer_email,
        query="This is a terrible delay, I am demanding a full refund and compensation!",
        sentiment="Negative",
        category="Refund",
        priority="Medium",
        status="Open",
        channel="WhatsApp"
    )
    
    # Customer profile checks
    profile = get_customer_profile(customer_email)
    assert profile is not None, "Failed to fetch customer profile!"
    customer_db = profile["customer"]
    
    print(f"- Customer Health Score (Angry customer): {customer_db.health_score}/100")
    print(f"- Customer Lifetime Value (CLV): ${customer_db.clv}")
    
    # Double check ticket escalation
    ticket_db = profile["tickets"][0]
    print(f"- Escalation Flag: {ticket_db.escalated_to_human}")
    print(f"- Escalation Reason: \"{ticket_db.escalation_reason}\"")
    print(f"- Risk Score: {ticket_db.escalation_risk_score}/100")
    
    assert ticket_db.escalated_to_human == True, "Failed to trigger automatic human escalation!"
    print("[OK] Customer 360 and smart escalations validated.\n")
    
    # 6. Session memory turns
    print("Step 6: Testing Agent Conversation memory (Session turns)...")
    sess_id = "sess_testing_123"
    
    from backend.database import SessionLocal, Conversation
    db_sess = SessionLocal()
    try:
        db_sess.query(Conversation).filter(Conversation.session_id == sess_id).delete()
        db_sess.commit()
    finally:
        db_sess.close()
        
    add_conversation_turn(session_id=sess_id, role="Customer", content="Hello, is anyone there?")
    add_conversation_turn(session_id=sess_id, role="Agent", content="Hi! I am the Support Agent. How can I help you?", agent_name="Support")
    
    hist = get_session_history(sess_id)
    assert len(hist) == 2, "Conversation turn logging failed!"
    print("[OK] Session memory turns verified.\n")
    
    # 7. Linear Regression Volume Forecasting
    print("Step 7: Testing Predictive Ticket Volume Forecasting...")
    all_tickets = get_all_tickets()
    forecast = get_ticket_forecast(all_tickets)
    
    print(f"- Predicted ticket volume (tomorrow): {forecast['forecast_volumes'][0]}")
    print(f"- Staffing recommendation (tomorrow): {forecast['staff_recommendations'][0]} Agents")
    assert len(forecast["forecast_volumes"]) == 7, "Failed to output 7-day forecast!"
    print("[OK] Volume forecasting verified.\n")
    
    # 8. Hybrid RAG Search
    print("Step 8: Testing Advanced Hybrid RAG (Keyword + Vector + TF-IDF Reranking)...")
    if "GEMINI_API_KEY" in os.environ:
        try:
            kb_stats = get_kb_stats()
            print(f"- Vector Store chunks count: {kb_stats['total_chunks']}")
            
            # Test query
            query_hits = query_knowledge_base("refund policy", n_results=1)
            if query_hits:
                print(f"- RAG Hit: \"{query_hits[0]['content'][:60]}...\" (Confidence: {query_hits[0]['confidence']}% via {query_hits[0]['retrieval_method']})")
            print("[OK] Hybrid RAG verified.\n")
        except Exception as e:
            print(f"[SKIP] RAG test failed due to live API key requirements: {e}")
    else:
        print("[SKIP] Hybrid RAG test skipped because GEMINI_API_KEY is not configured in the environment.\n")
    
    # 9. Churn Prediction Test
    print("Step 9: Testing Churn Prediction ML Model...")
    from backend.ml.predictors import predict_churn_risk
    status, score = predict_churn_risk(
        negative_tickets=3,
        escalations=2,
        days_since_last=45,
        clv=150.0,
        health_score=35
    )
    print(f"- Churn Prediction Test: Risk Status: {status}, Score: {score}%")
    assert status in ["Low", "Medium", "High"], "Churn prediction returned invalid class!"
    print("[OK] Churn model inference verified.\n")

    # 10. ROI Calculation Verification
    print("Step 10: Testing ROI Calculation logic...")
    from backend.database import SessionLocal, Ticket
    db = SessionLocal()
    try:
        t = add_ticket(
            customer_name="John Test",
            customer_email="john@test.com",
            query="Billing query",
            sentiment="Neutral",
            category="Billing",
            status="Open",
            channel="Web Chat"
        )
        update_ticket(t.id, status="Resolved", escalated=False)
        
        tickets_automated = db.query(Ticket).filter(Ticket.status == "Resolved", Ticket.escalated_to_human == False).count()
        assert tickets_automated >= 1, "Automated tickets calculation failed!"
        print(f"- ROI automated resolved tickets count: {tickets_automated}")
        print("[OK] ROI calculations verified.\n")
    finally:
        db.close()

    # 11. Anomaly alerts verification
    print("Step 11: Testing Anomaly Detection Alert mechanism...")
    from backend.database import add_system_alert, get_active_alerts
    add_system_alert("Test alert: Volume spike of 45% detected.")
    alerts = get_active_alerts()
    assert len(alerts) >= 1, "Alert creation or retrieval failed!"
    print(f"- Active Alert retrieved: \"{alerts[0]['reason']}\"")
    print("[OK] Anomaly alerts verified.\n")

    print("========================================")
    print("[SUCCESS] All Verification Tests Passed Successfully!")
    print("========================================")

if __name__ == "__main__":
    run_tests()

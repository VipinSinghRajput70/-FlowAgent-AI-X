import os
from dotenv import load_dotenv
load_dotenv()
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import hashlib

from backend.database import (
    init_db, get_all_tickets, update_ticket, 
    add_lead, get_all_leads, get_analytics,
    add_conversation_turn, get_session_history,
    get_customer_profile, log_audit, SessionLocal, User, Customer,
    set_config_value, get_all_documents, Document, IncomingMessage,
    CRMCard, get_all_crm_cards
)
from backend.vector_store import index_document, get_kb_stats, query_knowledge_base, delete_document_from_kb
from backend.agent_manager import AgentManager
from backend.ml.train_models import train_all
from backend.ml.predictors import load_models, predict_lead_score, simulate_scenario_metrics
from backend.ml.forecaster import get_ticket_forecast
from backend.security import create_access_token, decode_access_token, hash_password, verify_password, rate_limiter
import google.generativeai as genai

app = FastAPI(title="FlowAgent AI API Backend", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

# Static Files serving for Widget
from fastapi.staticfiles import StaticFiles
widget_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "widget")
os.makedirs(widget_dir, exist_ok=True)
app.mount("/widget", StaticFiles(directory=widget_dir), name="widget")

# -------------------------------------------------------------
# Security & Rate Limiting Middleware
# -------------------------------------------------------------

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Extract Gemini API Key from request headers
    gemini_key = request.headers.get("X-Gemini-API-Key")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        # Persist to database so it loads automatically on restart
        try:
            set_config_value("GEMINI_API_KEY", gemini_key)
        except Exception as e:
            print(f"Error saving GEMINI_API_KEY to config DB: {e}")

    # Exclude docs and health check from rate limits
    if request.url.path not in ["/api/health", "/docs", "/openapi.json"]:
        client_ip = request.client.host if request.client else "127.0.0.1"
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Too Many Requests. API Rate limit exceeded.")
    return await call_next(request)

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Credentials missing or invalid token scheme")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired or invalid signature")
    return payload

def get_manager_user(payload: dict = Depends(get_current_user)):
    if payload.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Forbidden. Manager role required.")
    return payload

# Pydantic Schemas
class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "Agent" # Manager, Agent

class UserLogin(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    customer_name: str
    customer_email: EmailStr
    query: str
    session_id: Optional[str] = "default_session"
    channel: Optional[str] = "Web Chat"
    auto_resolve: Optional[bool] = False
    image_data: Optional[str] = None
    voice_active: Optional[bool] = False

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent: Optional[str] = None
    response_draft: Optional[str] = None
    escalated: Optional[bool] = None

class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = "Unknown"
    requirements: str
    page_views: int = 1
    time_on_site: int = 30
    form_submitted: int = 0

# Metrics tracking
request_counts = {"total": 0, "chat": 0, "kb": 0}

# Initialize agents
agent_manager = None

@app.on_event("startup")
async def startup_event():
    global agent_manager
    init_db()
    
    # Load GEMINI_API_KEY from database configurations table
    from backend.database import get_config_value
    try:
        stored_key = get_config_value("GEMINI_API_KEY")
        if stored_key:
            os.environ["GEMINI_API_KEY"] = stored_key
            print("Successfully loaded GEMINI_API_KEY from database config table.")
    except Exception as e:
        print(f"Failed to load stored API Key: {e}")
        
    if not load_models():
        print("ML Models missing. Triggering training...")
        train_all()
        load_models()
        
    try:
        agent_manager = AgentManager()
    except Exception as e:
        print(f"Warning during agent manager startup: {e}. Live agent endpoints will remain locked until GEMINI_API_KEY is configured.")
        
    # Ingest default files if key is available
    try:
        stats = get_kb_stats()
        if stats["total_chunks"] == 0:
            create_default_docs()
            index_default_docs()
    except Exception as e:
        print(f"Warning during vector store startup: {e}. RAG document indexing will be locked until GEMINI_API_KEY is configured.")

def create_default_docs():
    faq_path = os.path.join(DOCS_DIR, "company_faq.txt")
    if not os.path.exists(faq_path):
        with open(faq_path, "w", encoding="utf-8") as f:
            f.write("""FlowAgent AI System FAQ
Q: What is FlowAgent AI?
A: FlowAgent AI is an advanced multi-agent business operations and customer support platform that automates customer messaging, sentiment detection, SQLite ticket recording, ML lead qualification, and business analytics.

Q: How much do your subscription plans cost?
A: Our plans are:
- Basic Plan: $29/month. Includes 1-agent operations, up to 1000 tickets/month, and basic email support.
- Pro Plan: $99/month. Includes multi-agent collaboration (up to 4 agents), 10,000 tickets/month, custom local ML models, and 24/7 ticket support.
- Enterprise Plan: Custom pricing (starting at $499/month). Includes unlimited agent orchestration, dedicated ChromaDB vector instances, custom API integrations, and SLA-based technical support.

Q: Do you offer a refund?
A: Yes, we provide a 14-day money-back guarantee for all basic and pro plans if you are unsatisfied with our platform. Please contact refund@flowagent.ai to request a refund.

Q: How do I change my account email?
A: Go to Settings in the user dashboard, click on Account Information, enter your new email address, and verify it using the confirmation code sent to your inbox.
""")
            
    policy_path = os.path.join(DOCS_DIR, "refund_policy.txt")
    if not os.path.exists(policy_path):
        with open(policy_path, "w", encoding="utf-8") as f:
            f.write("""FlowAgent AI Refund and Cancellation Policy
Last updated: June 2026

We want our customers to be completely satisfied. We offer a 14-day refund period from the initial date of purchase for our Basic and Pro subscription plans. 
If 14 days have passed since your purchase, unfortunately, we cannot offer you a refund or exchange.

To request a refund, please send an email to refund@flowagent.ai with the following details:
1. Account holder name and email.
2. Invoice or Transaction ID.
3. Reason for refund request.

Refund requests are typically processed within 3-5 business days. Once approved, the credit will automatically be applied to your credit card or original method of payment.
Enterprise agreements and custom setups are subject to separate contract terms and are generally non-refundable unless explicitly stated.
""")

def index_default_docs():
    db = SessionLocal()
    try:
        for filename in os.listdir(DOCS_DIR):
            filepath = os.path.join(DOCS_DIR, filename)
            if os.path.isfile(filepath):
                chunks_indexed = index_document(filepath, filename)
                # Register in SQL Document table if not exists
                existing = db.query(Document).filter(Document.filename == filename).first()
                if not existing:
                    new_doc = Document(filename=filename, filepath=filepath, chunks_count=chunks_indexed)
                    db.add(new_doc)
        db.commit()
    except Exception as e:
        print(f"Error in index_default_docs: {e}")
    finally:
        db.close()

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
def health_check():
    models_status = load_models()
    return {
        "status": "healthy",
        "ml_models_loaded": models_status,
        "api_key_configured": bool(os.environ.get("GEMINI_API_KEY"))
    }

@app.get("/metrics")
def prometheus_metrics():
    # Return plain text Prometheus style metrics
    t_stats = get_analytics()
    lines = [
        "# HELP flowagent_http_requests_total Total number of HTTP requests processed.",
        f"flowagent_http_requests_total {request_counts['total']}",
        "# HELP flowagent_tickets_total Total support tickets recorded in relational DB.",
        f"flowagent_tickets_total {t_stats['total_tickets']}",
        "# HELP flowagent_leads_total Total leads score qualified in SQLite.",
        f"flowagent_leads_total {t_stats['total_leads']}",
        "# HELP flowagent_csat_score Heuristic Customer Satisfaction score.",
        f"flowagent_csat_score {t_stats['csat_score']}",
        "# HELP flowagent_escalations_total Number of human escalation events flagged.",
        f"flowagent_escalations_total {t_stats['escalated_count']}"
    ]
    return "\n".join(lines)

# User registration & login routes
@app.post("/api/auth/register")
def register_user(user_data: UserRegister):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
            
        hashed = hash_password(user_data.password)
        new_user = User(username=user_data.username, password_hash=hashed, role=user_data.role)
        db.add(new_user)
        db.commit()
        
        log_audit(user_data.username, f"User registered successfully with role {user_data.role}")
        return {"message": "User created successfully"}
    finally:
        db.close()

@app.post("/api/auth/login")
def login_user(credentials: UserLogin):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == credentials.username).first()
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        token = create_access_token(data={"username": user.username, "role": user.role})
        log_audit(user.username, f"User logged in successfully")
        return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}
    finally:
        db.close()

# Agent Chat Interface
@app.post("/api/chat")
async def chat_interaction(request: ChatRequest, background_tasks: BackgroundTasks):
    global agent_manager
    request_counts["total"] += 1
    request_counts["chat"] += 1
    
    current_key = os.environ.get("GEMINI_API_KEY", "")
    if agent_manager is None or agent_manager.api_key != current_key:
        try:
            agent_manager = AgentManager()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to initialize AI Agents: {str(e)}")
        
    try:
        # Run agent manager pipeline
        response = agent_manager.run_query(
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            query=request.query,
            session_id=request.session_id,
            channel=request.channel,
            image_data=request.image_data,
            voice_active=request.voice_active
        )
        
        # Auto resolution trigger logic
        is_auto_resolved = False
        if request.auto_resolve and response.get("confidence", 30) >= 85:
            # Auto resolve ticket in background
            is_auto_resolved = True
            background_tasks.add_task(
                update_ticket, 
                ticket_id=response["ticket_id"], 
                status="Resolved",
                response_draft=f"AUTO-RESOLVED by Supervisor Agent: {response['final_answer']}"
            )
            response["auto_resolved"] = True
            
        # Log audit trail
        background_tasks.add_task(
            log_audit, 
            username="System", 
            action=f"Processed multi-agent query for {request.customer_email}. Auto-resolved: {is_auto_resolved}."
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-Agent error: {str(e)}")

# Core SQLite Database CRUD
@app.get("/api/tickets")
def get_tickets(current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    return get_all_tickets()

@app.put("/api/tickets/{ticket_id}")
def update_existing_ticket(ticket_id: int, ticket_data: TicketUpdate, current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    updated = update_ticket(
        ticket_id=ticket_id,
        status=ticket_data.status,
        priority=ticket_data.priority,
        assigned_agent=ticket_data.assigned_agent,
        response_draft=ticket_data.response_draft,
        escalated=ticket_data.escalated
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    log_audit(current_user["username"], f"Updated Ticket #{ticket_id} status={ticket_data.status} priority={ticket_data.priority}")
    return updated

@app.get("/api/leads")
def get_leads(current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    return get_all_leads()

@app.post("/api/leads")
def create_lead_manually(lead_data: LeadCreate, current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    lead_status, lead_score = predict_lead_score(
        page_views=lead_data.page_views,
        time_on_site=lead_data.time_on_site,
        form_submitted=lead_data.form_submitted,
        email=lead_data.email
    )
    
    lead = add_lead(
        name=lead_data.name,
        email=lead_data.email,
        company=lead_data.company,
        requirements=lead_data.requirements,
        lead_score=lead_score,
        lead_status=lead_status
    )
    
    log_audit(current_user["username"], f"Manually created Lead for {lead_data.email} - status={lead_status}")
    return lead

# Customer 360° Profile API
@app.get("/api/customers")
def get_all_customers_list(current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Customer
    db = SessionLocal()
    try:
        custs = db.query(Customer).order_by(Customer.health_score.asc()).all()
        return custs
    finally:
        db.close()

@app.get("/api/customers/{email}")
def get_customer_360_profile(email: str, current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    profile = get_customer_profile(email)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return profile

# Forecasting API
@app.get("/api/analytics/forecast")
def get_ticket_volume_forecast(current_user: dict = Depends(get_manager_user)):
    request_counts["total"] += 1
    tickets = get_all_tickets()
    forecast = get_ticket_forecast(tickets)
    return forecast

# Vector DB upload routes
@app.post("/api/kb/upload")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    request_counts["kb"] += 1
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        chunks_indexed = index_document(filepath, file.filename)
        
        # Register in relational database
        db = SessionLocal()
        try:
            existing = db.query(Document).filter(Document.filename == file.filename).first()
            if existing:
                existing.chunks_count = chunks_indexed
                existing.filepath = filepath
            else:
                new_doc = Document(filename=file.filename, filepath=filepath, chunks_count=chunks_indexed)
                db.add(new_doc)
            db.commit()
        finally:
            db.close()
            
        log_audit(current_user["username"], f"Indexed RAG document {file.filename} - {chunks_indexed} chunks.")
        
        return {
            "filename": file.filename,
            "status": "success",
            "chunks_indexed": chunks_indexed
        }
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/kb/stats")
def get_knowledge_base_stats():
    return get_kb_stats()

@app.get("/api/kb/search")
def search_knowledge_base(q: str, current_user: dict = Depends(get_current_user)):
    request_counts["total"] += 1
    try:
        return query_knowledge_base(q)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"RAG Database error: {str(e)}")

@app.get("/api/analytics")
def get_analytics_dashboard_data():
    return get_analytics()

@app.post("/api/train")
def retrain_ml_models(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_all)
    return {"message": "Model retraining started in the background."}

# System configuration GET/POST
@app.get("/api/config")
def get_system_config(current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, SystemConfig
    db = SessionLocal()
    try:
        cfgs = db.query(SystemConfig).all()
        config_dict = {}
        for c in cfgs:
            if c.key == "GEMINI_API_KEY":
                config_dict[c.key] = "********" if c.value else ""
            else:
                config_dict[c.key] = c.value
        return config_dict
    finally:
        db.close()

class ConfigUpdate(BaseModel):
    key: str
    value: str

@app.post("/api/config")
def update_system_config(cfg: ConfigUpdate, current_user: dict = Depends(get_current_user)):
    from backend.database import set_config_value
    set_config_value(cfg.key, cfg.value)
    if cfg.key == "GEMINI_API_KEY":
        os.environ["GEMINI_API_KEY"] = cfg.value
    return {"status": "success", "message": f"Configuration {cfg.key} updated successfully."}

# RAG Document management
@app.get("/api/kb/documents")
def list_kb_documents(current_user: dict = Depends(get_current_user)):
    return get_all_documents()

@app.delete("/api/kb/documents/{doc_id}")
def delete_kb_document(doc_id: int, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Document
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        filename = doc.filename
        
        # Delete from ChromaDB
        delete_document_from_kb(filename)
        
        # Delete file from local filesystem
        if os.path.exists(doc.filepath):
            try:
                os.remove(doc.filepath)
            except Exception as e:
                print(f"Error removing local file: {e}")
        
        # Delete from Relational DB
        db.delete(doc)
        db.commit()
        
        log_audit(current_user["username"], f"Deleted RAG document {filename}")
        return {"status": "success", "message": f"Document {filename} deleted successfully."}
    finally:
        db.close()

# Omnichannel Inbox message retrieval and injection
@app.get("/api/incoming-messages")
def get_omnichannel_messages(channel: Optional[str] = None, status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, IncomingMessage
    db = SessionLocal()
    try:
        q = db.query(IncomingMessage)
        if channel:
            q = q.filter(IncomingMessage.channel == channel)
        if status:
            q = q.filter(IncomingMessage.status == status)
        return q.order_by(IncomingMessage.created_at.desc()).all()
    finally:
        db.close()

class IncomingMessageCreate(BaseModel):
    sender: str
    email: EmailStr
    text: str
    channel: str

@app.post("/api/incoming-messages")
def create_incoming_message(msg: IncomingMessageCreate, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, IncomingMessage
    db = SessionLocal()
    try:
        new_msg = IncomingMessage(
            sender=msg.sender,
            email=msg.email,
            text=msg.text,
            channel=msg.channel,
            status="Pending"
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)
        return new_msg
    finally:
        db.close()

@app.post("/api/incoming-messages/{msg_id}/process")
async def process_incoming_message(msg_id: int, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, IncomingMessage
    db = SessionLocal()
    try:
        msg = db.query(IncomingMessage).filter(IncomingMessage.id == msg_id).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Incoming message not found")
            
        # Process using AgentManager
        global agent_manager
        current_key = os.environ.get("GEMINI_API_KEY", "")
        if agent_manager is None or agent_manager.api_key != current_key:
            try:
                agent_manager = AgentManager()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to initialize AI Agents: {str(e)}")
        
        response = agent_manager.run_query(
            customer_name=msg.sender,
            customer_email=msg.email,
            query=msg.text,
            session_id=f"session_{msg.email}",
            channel=msg.channel
        )
        
        # Update incoming message status to Processed
        msg.status = "Processed"
        db.commit()
        
        log_audit(current_user["username"], f"Processed omnichannel message #{msg_id} from {msg.email} via agent pipeline")
        return response
    finally:
        db.close()

# Decoupled Executive Copilot endpoint
class CopilotRequest(BaseModel):
    query: str

@app.post("/api/analytics/copilot")
def consult_executive_copilot(req: CopilotRequest, current_user: dict = Depends(get_current_user)):
    current_key = os.environ.get("GEMINI_API_KEY", "")
    if not current_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not set. Copilot requires a valid Gemini API key.")
        
    t_stats = get_analytics()
    prompt = f"""
    You are the Executive Copilot for FlowAgent AI.
    The manager asked: "{req.query}"
    System Analytics Stats: {t_stats}
    
    Provide a brief, data-driven analysis and suggest 2 practical operations actions based on this. Limit to 3-4 sentences.
    """
    try:
        genai.configure(api_key=current_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        res_cop = model.generate_content(prompt).text.strip()
        return {"analysis": res_cop}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot logic failed: {str(e)}")

# ROI Endpoint
@app.get("/api/analytics/roi")
def get_roi_analytics(current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Ticket
    db = SessionLocal()
    try:
        total_tickets = db.query(Ticket).count()
        tickets_automated = db.query(Ticket).filter(Ticket.status == "Resolved", Ticket.escalated_to_human == False).count()
        
        avg_handling_time_saved_minutes = 8
        total_hours_saved = (tickets_automated * avg_handling_time_saved_minutes) / 60.0
        cost_saved_inr = total_hours_saved * 250.0 # hourly rate ₹250
        automation_rate_percent = (tickets_automated / total_tickets * 100.0) if total_tickets > 0 else 0.0
        
        # Estimate CSAT improvement based on sentiment distribution
        pos_count = db.query(Ticket).filter(Ticket.sentiment == "Positive").count()
        neg_count = db.query(Ticket).filter(Ticket.sentiment == "Negative").count()
        csat_improvement_estimate = round(10.0 + (pos_count / (pos_count + neg_count + 1)) * 15.0 - (neg_count / (pos_count + neg_count + 1)) * 5.0, 1)
        
        # Narrative generation
        current_key = os.environ.get("GEMINI_API_KEY", "")
        narrative = ""
        if current_key:
            try:
                genai.configure(api_key=current_key)
                model_gem = genai.GenerativeModel("gemini-1.5-flash")
                prompt_roi = f"""
                You are the Operations ROI Analyst for FlowAgent AI.
                The company has automated {tickets_automated} customer support tickets this period.
                This saved {round(total_hours_saved, 1)} hours of agent time, translating to a direct cost savings of INR {int(cost_saved_inr)}.
                The automation rate is {round(automation_rate_percent, 1)}%.
                Write a concise 2-sentence narrative summarizing these savings in a professional, business-impact tone. Do not use markdown format.
                """
                narrative = model_gem.generate_content(prompt_roi).text.strip()
            except Exception:
                pass
                
        if not narrative:
            narrative = f"This period, FlowAgent AI automated {round(automation_rate_percent, 1)}% of support volume, saving approximately ₹{int(cost_saved_inr)} and {round(total_hours_saved, 1)} hours of manual agent handling time."
            
        return {
            "tickets_automated": tickets_automated,
            "total_tickets": total_tickets,
            "avg_handling_time_saved_minutes": avg_handling_time_saved_minutes,
            "total_hours_saved": round(total_hours_saved, 1),
            "cost_saved_inr": int(cost_saved_inr),
            "automation_rate_percent": round(automation_rate_percent, 1),
            "csat_improvement_estimate": csat_improvement_estimate,
            "narrative": narrative
        }
    finally:
        db.close()

# Public CORS widget endpoint
class WidgetChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/widget/chat")
async def widget_chat(req: WidgetChatRequest):
    global agent_manager
    current_key = os.environ.get("GEMINI_API_KEY", "")
    if agent_manager is None or agent_manager.api_key != current_key:
        try:
            agent_manager = AgentManager()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to initialize AI Agents: {str(e)}")
            
    try:
        response = agent_manager.run_query(
            customer_name="Web Visitor",
            customer_email="web.visitor@widget.com",
            query=req.message,
            session_id=req.session_id,
            channel="Web Chat"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Widget processing failure: {str(e)}")

# Churn prediction endpoint
@app.get("/api/customers/{email}/churn-risk")
def get_customer_churn_risk(email: str, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Customer, Ticket
    from backend.ml.predictors import predict_churn_risk
    import datetime
    db = SessionLocal()
    try:
        cust = db.query(Customer).filter(Customer.email == email).first()
        clv = cust.clv if cust else 0.0
        health_score = cust.health_score if cust else 100
        
        neg_tickets = db.query(Ticket).filter(Ticket.customer_email == email, Ticket.sentiment == "Negative").count()
        escalations = db.query(Ticket).filter(Ticket.customer_email == email, Ticket.escalated_to_human == True).count()
        
        last_ticket = db.query(Ticket).filter(Ticket.customer_email == email).order_by(Ticket.created_at.desc()).first()
        if last_ticket:
            days_since = (datetime.datetime.utcnow() - last_ticket.created_at).days
            days_since = max(days_since, 0)
        else:
            days_since = 30
            
        risk_class, risk_score = predict_churn_risk(
            negative_tickets=neg_tickets,
            escalations=escalations,
            days_since_last=days_since,
            clv=clv,
            health_score=health_score
        )
        
        return {
            "email": email,
            "churn_risk": risk_class,
            "churn_score": risk_score,
            "features": {
                "negative_tickets": neg_tickets,
                "escalations": escalations,
                "days_since_last": days_since,
                "clv": clv,
                "health_score": health_score
            }
        }
    finally:
        db.close()

# Active System Alerts endpoint
@app.get("/api/alerts/active")
def get_active_system_alerts(current_user: dict = Depends(get_current_user)):
    from backend.database import get_active_alerts
    return get_active_alerts()

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_active_system_alert(alert_id: int, current_user: dict = Depends(get_current_user)):
    from backend.database import resolve_alert
    success = resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "message": f"Alert #{alert_id} resolved."}

# Telegram Webhook Endpoint
@app.post("/api/webhooks/telegram")
async def telegram_webhook(request: Request):
    from backend.database import get_config_value
    token = get_config_value("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid JSON body"}
        
    if "message" not in body or "text" not in body["message"]:
        return {"status": "ignored", "reason": "no text message"}
        
    msg = body["message"]
    chat_id = msg["chat"]["id"]
    sender_name = msg["from"].get("first_name", "Telegram User")
    username = msg["from"].get("username", "tg_user")
    query_text = msg["text"]
    
    session_id = f"tg_{chat_id}"
    
    global agent_manager
    current_key = os.environ.get("GEMINI_API_KEY", "")
    if agent_manager is None or agent_manager.api_key != current_key:
        try:
            agent_manager = AgentManager()
        except Exception:
            pass
            
    if agent_manager:
        try:
            response = agent_manager.run_query(
                customer_name=sender_name,
                customer_email=f"{username}@telegram.com",
                query=query_text,
                session_id=session_id,
                channel="Telegram"
            )
            reply_text = response["final_answer"]
        except Exception as e:
            reply_text = f"Sorry, our AI agent pipeline encountered an issue. Please try again. Error: {e}"
    else:
        reply_text = "Sorry, our AI agents are currently offline. Gemini API key is missing."
        
    if token:
        import requests as req_libs
        try:
            req_libs.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": reply_text
                },
                timeout=5
            )
        except Exception as e:
            print(f"Error sending message to Telegram: {e}")
            
    return {"status": "success", "reply": reply_text}


# ─────────────────────────────────────────────────────────────────────────────
# CRM Cards Endpoint (Sales Agent Real-World Action Output)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/crm/cards")
def get_crm_cards(current_user: dict = Depends(get_current_user)):
    """Returns all CRM cards created by the Sales Agent for Hot leads."""
    return get_all_crm_cards()


# ─────────────────────────────────────────────────────────────────────────────
# Reflection Log Endpoint — returns last N audit reflection events
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/reflection/logs")
def get_reflection_logs(current_user: dict = Depends(get_current_user)):
    """Returns recent audit logs that contained a reflection/rejection event."""
    db = SessionLocal()
    try:
        from backend.database import AuditLog
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.action.like("%reflection%"))
            .order_by(AuditLog.timestamp.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": l.id,
                "username": l.username,
                "action": l.action,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ]
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────────────────────
# Upgraded Hackathon Endpoints (Digital Twin, Self-Healing, Campaigns, Meeting Reports)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/campaigns")
def get_campaigns(current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Campaign
    db = SessionLocal()
    try:
        camps = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
        return camps
    finally:
        db.close()

class SimulationRequest(BaseModel):
    staff_change: float
    price_change: float
    campaign_launch: bool

@app.post("/api/digital-twin/simulate")
def digital_twin_simulate(req: SimulationRequest, current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, SimulatedScenario
    
    metrics = simulate_scenario_metrics(req.staff_change, req.price_change, req.campaign_launch)
    
    db = SessionLocal()
    try:
        scenario = SimulatedScenario(
            scenario_name=f"Sim {datetime.utcnow().strftime('%M:%S')}",
            staff_change=req.staff_change,
            price_change=req.price_change,
            campaign_launch=req.campaign_launch,
            predicted_csat=metrics["predicted_csat"],
            predicted_backlog_latency=metrics["predicted_backlog_latency"],
            predicted_churn_rate=metrics["predicted_churn_rate"],
            predicted_roi_impact=metrics["predicted_roi_impact"]
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        
        log_audit(current_user["username"], f"Ran what-if simulation: staff={req.staff_change}%, price={req.price_change}%, campaign={req.campaign_launch}")
        
        return metrics
    finally:
        db.close()

@app.post("/api/kb/self-heal")
def self_heal_kb(current_user: dict = Depends(get_current_user)):
    from backend.database import SessionLocal, Ticket
    from backend.vector_store import index_document
    
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).filter(Ticket.sentiment == "Negative", Ticket.status != "Resolved").all()
        if not tickets:
            return {"status": "success", "healed": False, "message": "No negative unresolved complaints detected. Knowledge base is healthy."}
            
        cats = [t.category for t in tickets if t.category]
        if not cats:
            return {"status": "success", "healed": False, "message": "No complaint categories found to self-heal."}
            
        from collections import Counter
        top_cat = Counter(cats).most_common(1)[0][0]
        
        healed_content = f"""FlowAgent AI System Healed KB FAQ - {top_cat} Issues
Q: How does the system handle repeating unresolved customer issues in the {top_cat} category?
A: Our system curators generated this self-healing RAG FAQ page. All {top_cat} queries are automatically checked against historical ledger and escalated to the department supervisor within 15 minutes of failure logs.
"""
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
        healed_file = os.path.join(docs_dir, f"healed_{top_cat.lower().replace(' ', '_')}.txt")
        with open(healed_file, "w", encoding="utf-8") as f:
            f.write(healed_content)
            
        index_document(healed_file, os.path.basename(healed_file))
        
        # Register in SQLite Document table if not exists
        from backend.database import Document
        existing = db.query(Document).filter(Document.filename == os.path.basename(healed_file)).first()
        if not existing:
            new_doc = Document(filename=os.path.basename(healed_file), filepath=healed_file, chunks_count=1)
            db.add(new_doc)
            db.commit()
            
        log_audit(current_user["username"], f"Self-healed Knowledge Base FAQ generated for category: {top_cat}")
        return {
            "status": "success",
            "healed": True,
            "category": top_cat,
            "message": f"Successfully generated and indexed new FAQ page for recurring complaint category: {top_cat}."
        }
    finally:
        db.close()

@app.get("/api/reports/meeting")
def get_meeting_report(type: str = "daily", current_user: dict = Depends(get_current_user)):
    t_stats = get_analytics()
    
    report = f"""# 📈 FlowAgent AI X Executive Briefing - {type.upper()} REPORT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## 📊 Performance Indicators
* **Customer Satisfaction (CSAT)**: {t_stats['csat_score']}%
* **Total Inbound Tickets**: {t_stats['total_tickets']}
* **Unresolved Escalations**: {t_stats['escalated_count']}
* **Total Leads Qualified**: {t_stats['total_leads']}

## 🧠 Strategic Operations Actions
1. **Capacity Planning**: Ensure staffing matches projected daily ticket rates.
2. **Sentiment Alert**: Churn risk count is currently at {t_stats['churn_risk_count']}. Focus support on VIP profiles.
"""
    return {"report": report}

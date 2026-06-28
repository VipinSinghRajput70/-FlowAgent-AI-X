import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Setup database URL (supports PostgreSQL if configured in env, otherwise defaults to SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flowagent.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# PostgreSQL needs different connect_args than SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------------------
# ORM Model Definitions
# -------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(50), default="Agent")  # Manager, Agent

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    clv = Column(Float, default=0.0)  # Customer Lifetime Value
    health_score = Column(Integer, default=100)  # Customer Health Score (0-100)
    is_vip = Column(Boolean, default=False)
    total_tickets = Column(Integer, default=0)
    
    # Advanced Business Memory fields
    preferences = Column(Text, nullable=True, default="{}") # JSON of preferences
    interaction_frequency = Column(Integer, default=1)
    previous_discounts = Column(Text, nullable=True, default="[]") # JSON list of coupon codes
    sentiment_trend = Column(String(50), default="Stable") # Improving, Stable, Declining
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    budget = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0) # Percentage (e.g. 5.2)
    revenue_generated = Column(Float, default=0.0)
    status = Column(String(50), default="Active") # Active, Paused, Completed
    created_at = Column(DateTime, default=datetime.utcnow)

class SimulatedScenario(Base):
    __tablename__ = "simulated_scenarios"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_name = Column(String(100), nullable=False)
    staff_change = Column(Float, default=0.0) # Percentage e.g. -20% or +10%
    price_change = Column(Float, default=0.0) # Percentage
    campaign_launch = Column(Boolean, default=False)
    predicted_csat = Column(Float, default=85.0)
    predicted_backlog_latency = Column(Float, default=2.5) # hours
    predicted_churn_rate = Column(Float, default=5.0) # percentage
    predicted_roi_impact = Column(Float, default=0.0) # currency (INR)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)
    sentiment = Column(String(20), default="Neutral")
    category = Column(String(50), default="General Inquiry")
    priority = Column(String(20), default="Medium")
    status = Column(String(20), default="Open")
    assigned_agent = Column(String(50), default="Support Agent")
    response_draft = Column(Text, nullable=True)
    channel = Column(String(50), default="Web Chat")  # Web Chat, Email, WhatsApp, Telegram
    
    # Escalation fields
    escalated_to_human = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    escalation_risk_score = Column(Integer, default=0)  # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    requirements = Column(Text, nullable=True)
    lead_score = Column(Integer, default=50)
    lead_status = Column(String(20), default="Warm")  # Hot, Warm, Cold
    
    # Advanced Sales Intelligence fields
    conversion_probability = Column(Float, default=0.0)
    cross_sell_recommendation = Column(String(200), nullable=True)
    upsell_recommendation = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(50), nullable=False)  # Customer, Agent
    agent_name = Column(String(100), nullable=True)  # Support, Care, Sales, etc.
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    action = Column(Text, nullable=False)
    ip_address = Column(String(50), default="Unknown")
    timestamp = Column(DateTime, default=datetime.utcnow)

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(200), unique=True, nullable=False)
    filepath = Column(String(500), nullable=False)
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class IncomingMessage(Base):
    __tablename__ = "incoming_messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False)  # WhatsApp, Telegram, Email, Web Chat
    status = Column(String(50), default="Pending")  # Pending, Processed
    created_at = Column(DateTime, default=datetime.utcnow)

class CRMCard(Base):
    """Mock CRM card created by the Sales Agent for Hot leads."""
    __tablename__ = "crm_cards"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    lead_score = Column(Integer, default=50)
    lead_status = Column(String(20), default="Warm")   # Hot, Warm, Cold
    pitch_summary = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    stage = Column(String(50), default="Contacted")    # Qualified, Contacted, Demo Scheduled
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemAlert(Base):
    __tablename__ = "system_alerts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reason = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------------------------------------------------
# Database Initializer & CRUD Operations
# -------------------------------------------------------------

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed default admin user using bcrypt
        from backend.security import hash_password
        mgr = db.query(User).filter(User.username == "admin").first()
        if not mgr:
            pw_hash = hash_password("password")
            admin_user = User(username="admin", password_hash=pw_hash, role="Manager")
            db.add(admin_user)
            db.commit()
            
        # Seed default incoming messages if queue is empty
        msg_count = db.query(IncomingMessage).count()
        if msg_count == 0:
            default_msgs = [
                IncomingMessage(sender="Vipin Kumar", email="vipin@apex-industries.io", text="Hi, my payment failed but money was deducted from my account.", channel="WhatsApp", status="Pending"),
                IncomingMessage(sender="Amit Sharma", email="amit@sharma-tech.com", text="Are your support agents open on weekends? I need help setting up the API.", channel="WhatsApp", status="Pending"),
                IncomingMessage(sender="Rohit Patel", email="rohit@patel-corp.in", text="Hey, I need to unlock my account immediately. It got locked after 3 wrong password attempts.", channel="Telegram", status="Pending"),
                IncomingMessage(sender="HR Manager", email="hr@global-talent.org", text="Requesting a sales proposal quote for 50 Enterprise seats.", channel="Email", status="Pending"),
                IncomingMessage(sender="Web Visitor", email="anonymous@webchat.com", text="How do I cancel my subscription trial before I get charged?", channel="Web Chat", status="Pending")
            ]
            db.bulk_save_objects(default_msgs)
            db.commit()
            
        # Seed default campaigns if table is empty
        campaign_count = db.query(Campaign).count()
        if campaign_count == 0:
            default_campaigns = [
                Campaign(name="Summer Discount Offer 2026", budget=50000.0, conversion_rate=4.8, revenue_generated=240000.0, status="Completed"),
                Campaign(name="Enterprise Cloud Upgrade Campaign", budget=120000.0, conversion_rate=2.1, revenue_generated=580000.0, status="Active"),
                Campaign(name="Win-back Churn Prevention Campaign", budget=30000.0, conversion_rate=8.5, revenue_generated=150000.0, status="Active")
            ]
            db.bulk_save_objects(default_campaigns)
            db.commit()
            
        # Load API key configuration into environment if set
        for env_key in ["GEMINI_API_KEY", "RESEND_API_KEY", "DISCORD_WEBHOOK_URL"]:
            cfg = db.query(SystemConfig).filter(SystemConfig.key == env_key).first()
            if cfg and cfg.value:
                os.environ[env_key] = cfg.value
                print(f"Loaded {env_key} from database configuration.")
    finally:
        db.close()

def get_config_value(key: str, default=None) -> str:
    db = SessionLocal()
    try:
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return cfg.value if cfg else default
    finally:
        db.close()

def set_config_value(key: str, value: str):
    db = SessionLocal()
    try:
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if cfg:
            cfg.value = value
        else:
            cfg = SystemConfig(key=key, value=value)
            db.add(cfg)
        db.commit()
    finally:
        db.close()

def get_all_documents():
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
        # Convert to dict format to avoid session-closed serializing issues
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "filepath": d.filepath,
                "chunks_count": d.chunks_count,
                "created_at": d.created_at.isoformat()
            } for d in docs
        ]
    finally:
        db.close()

def add_system_alert(reason: str):
    db = SessionLocal()
    try:
        alert = SystemAlert(reason=reason, resolved=False)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    finally:
        db.close()

def get_active_alerts():
    db = SessionLocal()
    try:
        alerts = db.query(SystemAlert).filter(SystemAlert.resolved == False).order_by(SystemAlert.created_at.desc()).all()
        return [
            {
                "id": a.id,
                "reason": a.reason,
                "resolved": a.resolved,
                "created_at": a.created_at.isoformat()
            } for a in alerts
        ]
    finally:
        db.close()

def resolve_alert(alert_id: int):
    db = SessionLocal()
    try:
        alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
        if alert:
            alert.resolved = True
            db.commit()
            db.refresh(alert)
            return True
        return False
    finally:
        db.close()

def log_audit(username, action, ip_address="Unknown"):
    db = SessionLocal()
    try:
        log = AuditLog(username=username, action=action, ip_address=ip_address)
        db.add(log)
        db.commit()
    finally:
        db.close()

# Customer intelligence operations
def update_or_create_customer(name, email, lead_status="Cold", ticket_sentiment=None, ticket_status=None, ticket_priority=None):
    db = SessionLocal()
    try:
        cust = db.query(Customer).filter(Customer.email == email).first()
        if not cust:
            cust = Customer(name=name, email=email)
            db.add(cust)
            db.commit()
            db.refresh(cust)
        
        # Calculate dynamic values
        # 1. CLV
        # Hot = $1000, Warm = $500, Cold = $100
        leads = db.query(Lead).filter(Lead.email == email).all()
        clv_val = 0.0
        for l in leads:
            if l.lead_status == "Hot":
                clv_val += 1000.0
            elif l.lead_status == "Warm":
                clv_val += 500.0
            else:
                clv_val += 100.0
        cust.clv = clv_val
        
        # 2. VIP Flag
        if cust.clv >= 1500.0:
            cust.is_vip = True
            
        # 3. Tickets count
        tickets_count = db.query(Ticket).filter(Ticket.customer_email == email).count()
        cust.total_tickets = tickets_count
        
        # 4. Health Score
        # Start at 100. Subtract 15 for each Negative ticket, subtract 20 for High priority, add 10 for Resolved.
        health = 100
        all_tickets = db.query(Ticket).filter(Ticket.customer_email == email).all()
        for t in all_tickets:
            if t.sentiment == "Negative":
                health -= 15
            if t.priority == "High":
                health -= 20
            if t.status == "Resolved":
                health += 10
        
        cust.health_score = min(max(health, 0), 100)
        
        # 5. Interaction Frequency
        cust.interaction_frequency = (cust.interaction_frequency or 0) + 1
        
        # 6. Sentiment Trend
        last_3 = all_tickets[:3]
        if last_3:
            neg_count = sum(1 for t in last_3 if t.sentiment == "Negative")
            pos_count = sum(1 for t in last_3 if t.sentiment == "Positive")
            if neg_count >= 2:
                cust.sentiment_trend = "Declining"
            elif pos_count >= 2:
                cust.sentiment_trend = "Improving"
            else:
                cust.sentiment_trend = "Stable"
        else:
            cust.sentiment_trend = "Stable"
            
        db.commit()
        return cust
    finally:
        db.close()

# Ticket operations
def add_ticket(customer_name, customer_email, query, sentiment="Neutral", category="General Inquiry", priority="Medium", status="Open", assigned_agent="Support Agent", response_draft=None, channel="Web Chat"):
    db = SessionLocal()
    try:
        # Repeat complaint detection
        recent_count = db.query(Ticket).filter(
            Ticket.customer_email == customer_email,
            Ticket.sentiment == "Negative",
            Ticket.status != "Resolved"
        ).count()
        
        # Smart Escalation Calculation
        escalated = False
        esc_reason = ""
        risk = 30 # default baseline
        
        if sentiment == "Negative":
            risk += 30
        if priority == "High":
            risk += 20
        if recent_count >= 1:
            escalated = True
            risk += 20
            esc_reason += "Repeat complaint detected. "
            
        if risk >= 60:
            escalated = True
            esc_reason += f"High risk score ({risk}) calculated based on negative sentiment or high priority. "
            priority = "High"
            
        ticket = Ticket(
            customer_name=customer_name,
            customer_email=customer_email,
            query=query,
            sentiment=sentiment,
            category=category,
            priority=priority,
            status=status,
            assigned_agent=assigned_agent,
            response_draft=response_draft,
            channel=channel,
            escalated_to_human=escalated,
            escalation_reason=esc_reason.strip(),
            escalation_risk_score=min(risk, 100)
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Update customer analytics
        update_or_create_customer(customer_name, customer_email)
        return ticket
    finally:
        db.close()

def get_all_tickets():
    db = SessionLocal()
    try:
        return db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    finally:
        db.close()

def update_ticket(ticket_id, status=None, priority=None, assigned_agent=None, response_draft=None, escalated=None):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            if status:
                ticket.status = status
            if priority:
                ticket.priority = priority
            if assigned_agent:
                ticket.assigned_agent = assigned_agent
            if response_draft:
                ticket.response_draft = response_draft
            if escalated is not None:
                ticket.escalated_to_human = escalated
            db.commit()
            db.refresh(ticket)
            # Re-calculate customer metrics
            update_or_create_customer(ticket.customer_name, ticket.customer_email)
        return ticket
    finally:
        db.close()

# Lead operations
def add_lead(name, email, company, requirements, lead_score=50, lead_status="Warm"):
    db = SessionLocal()
    try:
        # Advanced Sales Intelligence (Heuristic recommendations & probability)
        prob = round(float(lead_score) / 100.0, 2)
        
        cross_sell = "None"
        upsell = "None"
        
        req_lower = requirements.lower()
        if lead_status == "Hot":
            upsell = "Upsell to Enterprise Suite Plan (Dedicated instances & SLAs)"
        elif lead_status == "Warm":
            upsell = "Upsell to Pro Annual Plan (Save 20% on multi-agent desk)"
            
        if any(w in req_lower for w in ["database", "postgres", "sync", "data", "backup"]):
            cross_sell = "Cross-sell SQL Vector Connector Add-on"
        elif any(w in req_lower for w in ["voice", "phone", "audio", "speech"]):
            cross_sell = "Cross-sell Voice complaint IVR Integration Package"
        elif any(w in req_lower for w in ["whatsapp", "telegram", "email", "sms"]):
            cross_sell = "Cross-sell Omnichannel Inbox Multi-channel Pack"
            
        lead = Lead(
            name=name,
            email=email,
            company=company,
            requirements=requirements,
            lead_score=lead_score,
            lead_status=lead_status,
            conversion_probability=prob,
            cross_sell_recommendation=cross_sell,
            upsell_recommendation=upsell
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Log/update customer entry
        update_or_create_customer(name, email, lead_status=lead_status)
        return lead
    finally:
        db.close()

def get_all_leads():
    db = SessionLocal()
    try:
        return db.query(Lead).order_by(Lead.created_at.desc()).all()
    finally:
        db.close()

# Conversation history (Agent Memory)
def add_conversation_turn(session_id, role, content, agent_name=None):
    db = SessionLocal()
    try:
        turn = Conversation(
            session_id=session_id,
            role=role,
            content=content,
            agent_name=agent_name
        )
        db.add(turn)
        db.commit()
        db.refresh(turn)
        return turn
    finally:
        db.close()

def get_session_history(session_id, limit=6):
    db = SessionLocal()
    try:
        turns = db.query(Conversation).filter(Conversation.session_id == session_id).order_by(Conversation.timestamp.desc()).limit(limit).all()
        # Return chronological order
        return turns[::-1]
    finally:
        db.close()

# Get customer profile 360 view
def get_customer_profile(email):
    db = SessionLocal()
    try:
        cust = db.query(Customer).filter(Customer.email == email).first()
        if not cust:
            return None
        tickets = db.query(Ticket).filter(Ticket.customer_email == email).order_by(Ticket.created_at.desc()).all()
        leads = db.query(Lead).filter(Lead.email == email).order_by(Lead.created_at.desc()).all()
        
        return {
            "customer": cust,
            "tickets": tickets,
            "leads": leads
        }
    finally:
        db.close()

def get_analytics():
    db = SessionLocal()
    try:
        total_tickets = db.query(Ticket).count()
        tickets_by_status = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        tickets_by_priority = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        tickets_by_sentiment = db.query(Ticket.sentiment, func.count(Ticket.id)).group_by(Ticket.sentiment).all()
        tickets_by_category = db.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
        
        total_leads = db.query(Lead).count()
        leads_by_status = db.query(Lead.lead_status, func.count(Lead.id)).group_by(Lead.lead_status).all()
        avg_lead_score = db.query(func.avg(Lead.lead_score)).scalar() or 0
        
        # Advanced statistics
        escalated_count = db.query(Ticket).filter(Ticket.escalated_to_human == True).count()
        vip_count = db.query(Customer).filter(Customer.is_vip == True).count()
        churn_risk_count = db.query(Customer).filter(Customer.health_score < 50).count()
        
        # Average CSAT heuristic (based on positive sentiment ratio)
        total_rated = db.query(Ticket).filter(Ticket.sentiment != "Neutral").count()
        pos_rated = db.query(Ticket).filter(Ticket.sentiment == "Positive").count()
        csat_score = round((pos_rated / total_rated) * 100, 1) if total_rated > 0 else 85.0
        
        return {
            "total_tickets": total_tickets,
            "tickets_by_status": dict(tickets_by_status),
            "tickets_by_priority": dict(tickets_by_priority),
            "tickets_by_sentiment": dict(tickets_by_sentiment),
            "tickets_by_category": dict(tickets_by_category),
            "total_leads": total_leads,
            "leads_by_status": dict(leads_by_status),
            "avg_lead_score": round(float(avg_lead_score), 2),
            "escalated_count": escalated_count,
            "vip_count": vip_count,
            "churn_risk_count": churn_risk_count,
            "csat_score": csat_score
        }
    finally:
        db.close()

def get_all_crm_cards():
    """Return all CRM cards sorted newest first."""
    db = SessionLocal()
    try:
        cards = db.query(CRMCard).order_by(CRMCard.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "lead_name": c.lead_name,
                "email": c.email,
                "company": c.company,
                "lead_score": c.lead_score,
                "lead_status": c.lead_status,
                "pitch_summary": c.pitch_summary,
                "requirements": c.requirements,
                "stage": c.stage,
                "email_sent": c.email_sent,
                "created_at": c.created_at.isoformat(),
            }
            for c in cards
        ]
    finally:
        db.close()

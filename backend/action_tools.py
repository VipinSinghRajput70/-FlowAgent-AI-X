"""
action_tools.py — Real-World Execution Tools for FlowAgent AI Agents

Provides "tool" functions that agents can call to take actual actions:
  - send_outreach_email  → Sends a transactional email via Resend API
  - send_discord_alert   → Posts an escalation alert to a Discord webhook
  - create_crm_card      → Creates a mock CRM card entry in SQLite

All tools degrade gracefully to simulation mode if API keys/URLs are not configured.
"""

import os
import json
import logging
import datetime
import httpx
from typing import Optional

logger = logging.getLogger("flowagent.action_tools")

# ─────────────────────────────────────────────────────────────────────────────
# 1. EMAIL TOOL — Resend API
# ─────────────────────────────────────────────────────────────────────────────

def send_outreach_email(
    to_email: str,
    to_name: str,
    lead_status: str,
    pitch_text: str,
    from_email: str = "FlowAgent AI <outreach@flowagent.ai>",
) -> dict:
    """
    Sends a hot-lead outreach email via the Resend API.
    Falls back to simulation mode if RESEND_API_KEY is not set.

    Returns:
        dict with keys: sent (bool), mode ('live' | 'simulation'), message_id or note
    """
    api_key = _get_config("RESEND_API_KEY")

    subject_map = {
        "Hot":  "🔥 Exclusive Enterprise Demo — Just for You",
        "Warm": "Your FlowAgent AI Trial is Ready",
        "Cold": "FlowAgent AI — Let's Connect",
    }
    subject = subject_map.get(lead_status, "FlowAgent AI — Let's Connect")

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; 
                background: #0f172a; color: #e2e8f0; padding: 32px; border-radius: 12px;">
        <h2 style="color: #00f2fe; margin-bottom: 8px;">FlowAgent AI</h2>
        <p style="color: #94a3b8; font-size: 13px; margin-top: 0;">Intelligent Business Operations Platform</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
        <p>Hi <strong>{to_name}</strong>,</p>
        <p style="line-height: 1.7;">{pitch_text}</p>
        <a href="https://calendly.com/flowagent/demo" 
           style="display: inline-block; margin-top: 20px; padding: 12px 28px; 
                  background: linear-gradient(135deg, #00f2fe, #4f46e5); 
                  color: #fff; border-radius: 8px; text-decoration: none; font-weight: bold;">
            Book a 15-min Demo Call
        </a>
        <p style="margin-top: 30px; font-size: 12px; color: #64748b;">
            FlowAgent AI • Enterprise Automation Platform<br>
            To unsubscribe, reply STOP.
        </p>
    </div>
    """

    if not api_key:
        # ── Simulation Mode ──
        note = (
            f"[SIMULATION] Would send '{subject}' to {to_email}. "
            "Set RESEND_API_KEY in config to send real emails."
        )
        logger.info(note)
        return {"sent": True, "mode": "simulation", "note": note, "to": to_email}

    # ── Live Mode via Resend ──
    try:
        import resend  # type: ignore
        resend.api_key = api_key
        response = resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        msg_id = response.get("id", "unknown")
        logger.info(f"Resend email sent to {to_email} — ID: {msg_id}")
        return {"sent": True, "mode": "live", "message_id": msg_id, "to": to_email}
    except Exception as e:
        logger.error(f"Resend email failed: {e}. Falling back to simulation.")
        return {
            "sent": False,
            "mode": "simulation",
            "note": f"Resend failed ({e}). Simulation logged.",
            "to": to_email,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. DISCORD WEBHOOK TOOL — Escalation Alerts
# ─────────────────────────────────────────────────────────────────────────────

def send_discord_alert(
    ticket_id: int,
    customer_name: str,
    customer_email: str,
    escalation_reason: str,
    priority: str = "High",
    sentiment: str = "Negative",
) -> dict:
    """
    Sends an escalation alert to a Discord channel via webhook.
    Falls back to simulation mode if DISCORD_WEBHOOK_URL is not set.

    Returns:
        dict with keys: sent (bool), mode ('live' | 'simulation'), status_code or note
    """
    webhook_url = _get_config("DISCORD_WEBHOOK_URL")

    priority_color = 0xFF4444 if priority == "High" else (0xFFA500 if priority == "Medium" else 0x44FF44)

    payload = {
        "username": "FlowAgent AI — Escalation Bot",
        "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png",
        "embeds": [
            {
                "title": f"🚨 Human Escalation Required — Ticket #{ticket_id}",
                "color": priority_color,
                "fields": [
                    {"name": "👤 Customer", "value": customer_name, "inline": True},
                    {"name": "📧 Email", "value": customer_email, "inline": True},
                    {"name": "⚠️ Priority", "value": priority, "inline": True},
                    {"name": "😤 Sentiment", "value": sentiment, "inline": True},
                    {"name": "📋 Escalation Reason", "value": escalation_reason, "inline": False},
                ],
                "footer": {"text": "FlowAgent AI • Automated Escalation System"},
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        ],
    }

    if not webhook_url:
        note = (
            f"[SIMULATION] Discord alert for Ticket #{ticket_id} ({customer_name}) "
            "would be sent. Set DISCORD_WEBHOOK_URL in config to send real alerts."
        )
        logger.info(note)
        return {"sent": True, "mode": "simulation", "note": note}

    # ── Live Mode ──
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(webhook_url, json=payload)
            resp.raise_for_status()
        logger.info(f"Discord alert sent for Ticket #{ticket_id} — Status: {resp.status_code}")
        return {"sent": True, "mode": "live", "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}. Falling back to simulation.")
        return {
            "sent": False,
            "mode": "simulation",
            "note": f"Discord webhook failed ({e}). Simulation logged.",
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. CRM CARD TOOL — SQLite Mock CRM
# ─────────────────────────────────────────────────────────────────────────────

def create_crm_card(
    lead_name: str,
    email: str,
    company: str,
    lead_score: int,
    lead_status: str,
    pitch_summary: str,
    requirements: str = "",
) -> dict:
    """
    Creates a CRM-style lead card in the SQLite database.
    Simulates Trello/HubSpot card creation.

    Returns:
        dict with keys: card_id, card_url, stage, created
    """
    try:
        from backend.database import SessionLocal, CRMCard  # imported here to avoid circular imports

        db = SessionLocal()
        try:
            card = CRMCard(
                lead_name=lead_name,
                email=email,
                company=company,
                lead_score=lead_score,
                lead_status=lead_status,
                pitch_summary=pitch_summary,
                requirements=requirements,
                stage="Qualified" if lead_status == "Hot" else "Contacted",
            )
            db.add(card)
            db.commit()
            db.refresh(card)

            card_url = f"https://crm.flowagent.ai/leads/{card.id}"
            logger.info(f"CRM card created for {lead_name} ({email}) — Card #{card.id}")
            return {
                "card_id": card.id,
                "card_url": card_url,
                "stage": card.stage,
                "created": True,
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"CRM card creation failed: {e}")
        return {"card_id": None, "card_url": None, "stage": None, "created": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Internal helper: read config from DB or environment
# ─────────────────────────────────────────────────────────────────────────────

def _get_config(key: str) -> Optional[str]:
    """Reads config from environment first, then falls back to DB config table."""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        from backend.database import get_config_value
        return get_config_value(key) or ""
    except Exception:
        return ""

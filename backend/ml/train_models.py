import os
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Setup paths
ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. Sentiment Model Data and Training
# -------------------------------------------------------------
def train_sentiment_model():
    print("Training Sentiment Analysis Model...")
    
    # Synthetic sentences for Sentiment
    data = {
        "text": [
            # Positive
            "I love this product, it works perfectly!",
            "Great customer support, they resolved my issue in minutes.",
            "Highly recommended, very fast delivery and good quality.",
            "Wow, this is amazing! Thank you so much.",
            "Excellent service, very friendly agent.",
            "So happy with my purchase, 5 stars!",
            "Fantastic platform, saved us so much time.",
            "Best support team ever, very polite.",
            "The new update is brilliant, love the UI.",
            "Satisfied customer, everything is great.",
            "bahut badhiya service hai, mazaa aa gaya!",
            "ekdum perfect chal raha hai, thank you",
            "bahut achha laga support team se baat karke",
            "superb platform hai, fast delivery",
            
            # Neutral
            "What are your working hours?",
            "How do I update my profile picture?",
            "Can I get the invoice for my last purchase?",
            "Is there a documentation available for the API?",
            "I have a question about my subscription.",
            "When will my order be shipped?",
            "Can you tell me how to reset my password?",
            "I am looking for your product catalog.",
            "Please send the contract to my email.",
            "What features are included in the basic plan?",
            "kya mujhe apna invoice mil sakta hai?",
            "password reset karne ka kya tareeqa hai?",
            "app par profile update kaise karein?",
            "basic plan me kya features hain?",
            
            # Negative
            "My order is delayed and I am very upset!",
            "This is the worst customer service, no one is answering.",
            "The app keeps crashing, I want a refund.",
            "I was double charged and I am extremely angry.",
            "This product is defective and doesn't work at all.",
            "You guys are useless, why is my account locked?",
            "Horrible experience, I want my money back immediately.",
            "Terrible performance, it is so slow.",
            "I've been waiting for three days, this is unacceptable.",
            "Your website is broken, I cannot log in.",
            "mera order abhi tak nahi aaya, bahut bura experience hai!",
            "faltu app hai, baar baar crash ho raha hai, refund chahiye",
            "double charge ho gaya aur account lock ho gaya",
            "worst customer support, koi jawab nahi de raha"
        ] * 15,  # Multiply to have a decent dataset size
        "label": (["Positive"] * 14 + ["Neutral"] * 14 + ["Negative"] * 14) * 15
    }
    
    df = pd.DataFrame(data)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=500, stop_words='english', ngram_range=(1, 2))),
        ('clf', LogisticRegression(C=1.0, max_iter=200))
    ])
    
    pipeline.fit(df['text'], df['label'])
    
    joblib.dump(pipeline, os.path.join(MODELS_DIR, "sentiment_model.joblib"))
    print("Sentiment model saved.")

# -------------------------------------------------------------
# 2. Ticket Classification Model Data and Training
# -------------------------------------------------------------
def train_ticket_classifier():
    print("Training Ticket Classification Model...")
    
    # Synthetic sentences for Categories: Billing, Technical, Account, Refund, General Inquiry
    data = {
        "text": [
            # Billing
            "Where is my invoice?",
            "I was charged twice for the subscription.",
            "Payment failed but my bank account was debited.",
            "How do I update my credit card details?",
            "My payment is not going through, help.",
            "I need a receipt for my tax filings.",
            "Is there a billing error on my account?",
            "Why did the subscription price change?",
            "Can I pay via PayPal instead of card?",
            "My transaction was declined.",
            "invoice kidhar hai?",
            "double payment cut gaya bank se",
            "payment decline ho raha hai baar baar",
            
            # Technical
            "The server is throwing a 500 internal server error.",
            "I cannot connect to the API endpoint.",
            "The app crashes every time I upload a file.",
            "How do I install the SDK on Python 3.12?",
            "I'm getting a connection timeout on your website.",
            "The dashboard is not loading database metrics.",
            "Integration setup failed for webhook.",
            "I see a blank screen on the login page.",
            "My database connection is failing.",
            "Is the website down right now?",
            "500 server error aa raha hai link pe",
            "api connect nahi ho raha code me",
            "website down hai kya, chal nahi rahi",
            
            # Account
            "I forgot my password, please send reset link.",
            "How can I change my primary email address?",
            "My account has been locked due to wrong attempts.",
            "How do I delete my account permanently?",
            "I want to merge two accounts.",
            "Can I add another team member to my organization?",
            "I am unable to login, says user does not exist.",
            "Update my account details and name.",
            "How do I enable two-factor authentication?",
            "My profile is not showing correct roles.",
            "password bhool gaya, link bhejo reset ka",
            "account lock ho gaya hai, unlock kaise karein?",
            "email address change karna hai profile me",
            
            # Refund
            "I want to cancel my subscription and get a refund.",
            "The product did not work, please refund my money.",
            "I was charged after cancelling my free trial, refund me.",
            "Can I get a money-back guarantee refund?",
            "I am not satisfied and request a full refund.",
            "Where is my refund for order #1234?",
            "Cancel my order and give my money back.",
            "You promised a refund, but I haven't received it.",
            "Accidentally purchased twice, please refund one.",
            "I request a refund for the downtime yesterday.",
            "mujhe apna refund wapas chahiye",
            "subscription cancel karo aur money refund karo",
            "galat charge kiya, refund do",
            
            # General Inquiry
            "What is your pricing plans list?",
            "Do support Salesforce integration?",
            "I want to request a sales demo of your software.",
            "Where can I find your user guides?",
            "What is the difference between Pro and Enterprise?",
            "Can I get a custom quote for a large team?",
            "Are your agents powered by Gemini or GPT?",
            "Do you have a free tier plan?",
            "What are your business hours?",
            "How do I contact sales?",
            "pricing plans list kya hai aapki?",
            "sales demo book karna hai mujhe",
            "free tier plan available hai kya?"
        ] * 12,
        "label": (["Billing"] * 13 + ["Technical"] * 13 + ["Account"] * 13 + ["Refund"] * 13 + ["General Inquiry"] * 13) * 12
    }
    
    df = pd.DataFrame(data)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=600, stop_words='english', ngram_range=(1, 2))),
        ('clf', LogisticRegression(C=1.2, max_iter=200))
    ])
    
    pipeline.fit(df['text'], df['label'])
    
    joblib.dump(pipeline, os.path.join(MODELS_DIR, "ticket_classifier.joblib"))
    print("Ticket classification model saved.")

# -------------------------------------------------------------
# 3. Lead Scoring Model Data and Training
# -------------------------------------------------------------
def train_lead_scorer():
    print("Training Lead Scoring Model...")
    
    # Generate synthetic lead feature dataset
    np.random.seed(42)
    n_samples = 1000
    
    # Features
    page_views = np.random.randint(1, 30, size=n_samples)
    time_on_site = np.random.randint(10, 1800, size=n_samples)
    form_submitted = np.random.choice([0, 1], size=n_samples, p=[0.6, 0.4])
    email_type = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])  # 1 = Professional, 0 = Public
    interaction_count = np.random.randint(1, 10, size=n_samples)
    
    # Define rules to calculate synthetic target status
    # Hot = 2, Warm = 1, Cold = 0
    scores = (
        page_views * 1.5 + 
        (time_on_site / 120.0) * 2.0 + 
        form_submitted * 25.0 + 
        email_type * 15.0 + 
        interaction_count * 3.0
    )
    
    # Normalize score to 0-100
    min_s, max_s = scores.min(), scores.max()
    normalized_scores = ((scores - min_s) / (max_s - min_s)) * 100
    
    # Classes
    labels = []
    for s in normalized_scores:
        if s >= 60:
            labels.append("Hot")
        elif s >= 35:
            labels.append("Warm")
        else:
            labels.append("Cold")
            
    df = pd.DataFrame({
        "page_views": page_views,
        "time_on_site": time_on_site,
        "form_submitted": form_submitted,
        "email_type": email_type,
        "interaction_count": interaction_count,
        "label": labels
    })
    
    # Split features and target
    X = df[["page_views", "time_on_site", "form_submitted", "email_type", "interaction_count"]]
    y = df["label"]
    
    # Create Pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42))
    ])
    
    pipeline.fit(X, y)
    
    joblib.dump(pipeline, os.path.join(MODELS_DIR, "lead_scorer.joblib"))
    print("Lead scoring model saved.")

def train_all():
    train_sentiment_model()
    train_ticket_classifier()
    train_lead_scorer()
    from backend.ml.churn_model import train_churn_model
    train_churn_model()
    print("All ML models trained successfully!")

if __name__ == "__main__":
    train_all()

import os
import sys
import subprocess
import time
import signal

def check_and_train_ml():
    print("Checking ML models status...")
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "ml", "models")
    model_files = ["sentiment_model.joblib", "ticket_classifier.joblib", "lead_scorer.joblib"]
    
    missing = False
    for f in model_files:
        if not os.path.exists(os.path.join(models_dir, f)):
            missing = True
            break
            
    if missing:
        print("ML model files are missing. Training them now using train_models.py...")
        try:
            train_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "ml", "train_models.py")
            subprocess.run([sys.executable, train_script], check=True)
            print("ML model training completed successfully!")
        except Exception as e:
            print(f"Error training ML models: {e}")
            sys.exit(1)
    else:
        print("All ML models are present.")

def main():
    # Configure UTF-8 encoding on Windows to prevent UnicodeEncodeErrors
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # Ensure correct working directory
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(workspace_dir)
    
    # 1. Train models if necessary
    check_and_train_ml()
    
    print("\nStarting FlowAgent AI Application Suite...")
    
    # 2. Start FastAPI Backend (port 8000)
    print("Launching FastAPI Backend on http://localhost:8000...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=None,
        stderr=None
    )
    
    # 3. Start Streamlit Frontend (port 8501)
    print("Launching Streamlit UI Dashboard on http://localhost:8501...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501"],
        stdout=None,
        stderr=None
    )
    
    # Wait a bit and check if processes are running
    time.sleep(3)
    
    if backend_process.poll() is not None:
        print("Error: FastAPI Backend failed to start. Please check the console logs above.")
        sys.exit(1)
        
    if frontend_process.poll() is not None:
        print("Error: Streamlit UI failed to start. Please check the console logs above.")
        backend_process.terminate()
        sys.exit(1)
        
    print("\n--------------------------------------------------------------")
    print("[RUNNING] FlowAgent AI is now running!")
    print("-> Backend API Documentation: http://localhost:8000/docs")
    print("-> Streamlit Dashboard UI:    http://localhost:8501")
    print("Press Ctrl+C to terminate both servers.")
    print("--------------------------------------------------------------\n")
    
    # Print process output in real-time or just sleep until interrupted
    try:
        while True:
            # Check if any process exited
            if backend_process.poll() is not None:
                print("FastAPI Backend process terminated unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("Streamlit Frontend process terminated unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
    finally:
        # Clean termination
        try:
            backend_process.terminate()
            print("FastAPI Backend terminated.")
        except Exception:
            pass
        try:
            frontend_process.terminate()
            print("Streamlit UI terminated.")
        except Exception:
            pass
            
if __name__ == "__main__":
    main()

import os
import subprocess
import sys
import time

print("--- AuraPronounce Production Process Manager ---")

# 1. Run database initialization
print("Initializing database...")
try:
    subprocess.run([sys.executable, "-m", "app.db_init"], check=True)
    print("Database initialization successful.")
except subprocess.CalledProcessError as e:
    print(f"Database initialization failed: {e}")
    sys.exit(1)

# 2. Spawn Celery Worker
print("Starting Celery background worker...")
celery_args = [
    sys.executable, "-m", "celery", 
    "-A", "app.worker.celery_app", 
    "worker", 
    "--loglevel=info",
    "--concurrency=1",
    "--pool=solo"
]
celery_proc = subprocess.Popen(celery_args, stdout=sys.stdout, stderr=sys.stderr)

# 3. Spawn Uvicorn API Server
port = os.environ.get("PORT", "8000")
print(f"Starting Uvicorn API server on port {port}...")
uvicorn_args = [
    sys.executable, "-m", "uvicorn", 
    "app.main:app", 
    "--host", "0.0.0.0", 
    "--port", port
]
uvicorn_proc = subprocess.Popen(uvicorn_args, stdout=sys.stdout, stderr=sys.stderr)

# 4. Monitor processes
try:
    while True:
        # Check status of child processes
        celery_status = celery_proc.poll()
        uvicorn_status = uvicorn_proc.poll()
        
        if celery_status is not None:
            print(f"[FATAL] Celery worker exited with code {celery_status}. Exiting...")
            uvicorn_proc.terminate()
            sys.exit(celery_status)
            
        if uvicorn_status is not None:
            print(f"[FATAL] Uvicorn server exited with code {uvicorn_status}. Exiting...")
            celery_proc.terminate()
            sys.exit(uvicorn_status)
            
        time.sleep(2)
except KeyboardInterrupt:
    print("Shutting down processes...")
    celery_proc.terminate()
    uvicorn_proc.terminate()
    sys.exit(0)
except Exception as e:
    print(f"Error in process monitor: {e}")
    celery_proc.terminate()
    uvicorn_proc.terminate()
    sys.exit(1)

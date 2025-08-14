import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

body = {
    "id": "01988482-a728-7755-87ae-3566699c362c",
    "memberId": "0197da84-b499-74e3-9cc7-1fe101fce7da"
}

# Ensure the directory exists
log_dir = "10_requests_Async"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = os.path.join(log_dir, "requests.log")
print(f"Opening log file: {log_file_path}")

try:
    file = open(log_file_path, "w")
    print(f"Successfully opened log file: {log_file_path}")
except Exception as e:
    print(f"Error opening log file: {e}")
    # Fallback to current directory
    file = open("requests.log", "w")
    print("Falling back to requests.log in current directory")

import threading
import concurrent.futures

def create_session():
    """Create a session with connection pooling and retry logic"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )
    
    # Configure adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=30,
        max_retries=retry_strategy
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def make_request(request_id, session):
    start_time = time.time()
    start_msg = f"Request {request_id}: Starting at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}"
    print(start_msg)
    
    try:
        response = session.post(
            "http://localhost:5001/extractdata", 
            json=body,
            timeout=(10, 120)  # (connect_timeout, read_timeout)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        success_msg = f"Request {request_id}: Completed in {duration:.3f} seconds (Status: {response.status_code})"
        print(success_msg)
        
        log_msg = f"Request {request_id}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} => took {duration:.3f} seconds (Status: {response.status_code})\n"
        try:
            file.write(log_msg)
            file.flush()  # Force write to disk
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        return request_id, start_time, duration, response.status_code
        
    except requests.exceptions.Timeout as e:
        end_time = time.time()
        duration = end_time - start_time
        timeout_msg = f"Request {request_id}: Timeout after {duration:.3f} seconds"
        print(timeout_msg)
        
        log_msg = f"Request {request_id}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} => TIMEOUT after {duration:.3f} seconds\n"
        try:
            file.write(log_msg)
            file.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        return request_id, start_time, duration, "TIMEOUT"
        
    except requests.exceptions.ConnectionError as e:
        end_time = time.time()
        duration = end_time - start_time
        conn_msg = f"Request {request_id}: Connection error after {duration:.3f} seconds: {e}"
        print(conn_msg)
        
        log_msg = f"Request {request_id}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} => CONNECTION_ERROR after {duration:.3f} seconds: {e}\n"
        try:
            file.write(log_msg)
            file.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        return request_id, start_time, duration, "CONNECTION_ERROR"
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        exc_msg = f"Request {request_id}: Exception after {duration:.3f} seconds: {e}"
        print(exc_msg)
        
        log_msg = f"Request {request_id}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} => EXCEPTION after {duration:.3f} seconds: {e}\n"
        try:
            file.write(log_msg)
            file.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        return request_id, start_time, duration, "EXCEPTION"

# Use ThreadPoolExecutor to send all requests in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
    # Create a session for each thread to avoid connection sharing issues
    sessions = [create_session() for _ in range(30)]
    
    futures = [executor.submit(make_request, i+1, sessions[i]) for i in range(30)]
    
    # Wait for all requests to complete
    completed = 0
    failed = 0
    
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            completed += 1
            if isinstance(result[3], str) and result[3] != "200":
                failed += 1
        except Exception as exc:
            print(f'Request generated an exception: {exc}')
            failed += 1

summary_msg = f"\nLoad test completed:\nTotal requests: 30\nCompleted: {completed}\nFailed: {failed}\nSuccess rate: {((completed - failed) / 30 * 100):.1f}%"
print(summary_msg)

try:
    file.write(summary_msg + "\n")
    file.flush()
except Exception as e:
    print(f"Error writing summary to log file: {e}")

file.close()
print(f"Log file closed. Check: {log_file_path}")
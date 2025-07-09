import threading
import time
from queue import Queue
from services.gmail_auth import get_gmail_service
from utils.email_utils import fetch_new_emails
from handlers.email_handler import handle_email

POLLING_INTERVAL = 5
NUM_WORKER_THREADS = 5

email_queue = Queue()
last_processed_time = time.time()

def email_worker(service):
    while True:
        msg_id = email_queue.get()
        if msg_id is None:
            break

        try:
            handle_email(service, msg_id)  # Pass only msg_id as expected
        except Exception as e:
            print(f"[❌ ERROR] Failed to process email {msg_id}: {e}")
        finally:
            email_queue.task_done()

def email_watcher(service):
    global last_processed_time
    print(f"📬 Email auto-responder started. Watching for emails after {time.ctime(last_processed_time)}")

    while True:
        try:
            new_emails = fetch_new_emails(service, last_processed_time)
            if new_emails:
                print(f"📥 {len(new_emails)} new email(s) found")

                max_timestamp = last_processed_time
                for email in new_emails:
                    email_queue.put(email['id'])  # Put msg_id only
                    if email['timestamp'] > max_timestamp:
                        max_timestamp = email['timestamp']

                last_processed_time = max_timestamp
            else:
                print("⏳ No new emails.")
        except Exception as e:
            print(f"[❌ ERROR] Fetching emails failed: {e}")

        time.sleep(POLLING_INTERVAL)

def main():
    print("🚀 Initializing Gmail service...")
    service = get_gmail_service()

    for i in range(NUM_WORKER_THREADS):
        t = threading.Thread(target=email_worker, args=(service,), daemon=True)
        t.start()
        print(f"🧵 Started worker thread #{i + 1}")

    try:
        email_watcher(service)
    except KeyboardInterrupt:
        print("🛑 Gracefully shutting down...")
        for _ in range(NUM_WORKER_THREADS):
            email_queue.put(None)
        email_queue.join()

if __name__ == "__main__":
    main()

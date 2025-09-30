import requests
import json
import time
import os
import uuid
import nest_asyncio
import sys
nest_asyncio.apply()
from websocket import create_connection
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) 
from e2e_helpers.prom import push_e2e_result

ENDPOINT_URL = os.getenv("URL")
USER = os.getenv("USER")
TOKEN = os.getenv("TOKEN")
SERVICE = os.getenv("SERVICE")
ENDPOINT_WS = os.getenv("SERVICE_WS")


class jupyter_test:
    def __init__(self):
        self.endpoint = ENDPOINT_URL
        self.endpoint_ws = ENDPOINT_WS
        self.user = USER
        self.token = TOKEN
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

    def status_code(self, response):
        if not 200 <= response.status_code <= 299:
            flag = 0
        else:
            flag = 1
        return flag

    def start_server(self):
        r = requests.post(f"{self.endpoint}/hub/api/users/{self.user}/server", 
                          headers=self.headers)
        return self.status_code(r)
    
    def wait_start(self):
        timeout = 300 
        interval = 5   
        elapsed = 0

        while elapsed < timeout:
            status = requests.get(f"{self.endpoint}/hub/api/users/{self.user}", headers=self.headers).json()
            if status.get("servers", {}).get("", {}).get("ready", False):
                print("Server is ready!")
                break
            time.sleep(interval)
            elapsed += interval
        else:
            raise TimeoutError("Server did not start within the expected time.")
    
    def start_kernel(self):
        r = requests.post(f"{self.endpoint}/user/{self.user}/api/kernels", 
                          headers=self.headers)
        return self.status_code(r), r.json()["id"]
    
    def start_session(self, kernel_id):
        session_payload = {
            "name": "",  
            "path": "api",  
            "type": "notebook", 
            "kernel": {"id": kernel_id}
        }

        r = requests.post(f"{self.endpoint}/user/{self.user}/api/sessions", 
                          json=session_payload, 
                          headers=self.headers)
        return self.status_code(r)
    
    def create_websocket(self, kernel_id):
        ws_url = f"wss://{self.endpoint_ws}/user/{self.user}/api/kernels/{kernel_id}/channels"
        code_to_run = """
        for i in range(3):
            print("Hello from API", i)
        """

        msg_id = str(uuid.uuid4())
        execute_msg = {
            "header": {"msg_type": "execute_request", "msg_id": msg_id},
            "parent_header": {},
            "metadata": {},
            "content": {"code": code_to_run, "silent": False}
        }

        headers_ws = [f"Authorization: token {self.token}"]

        ws = create_connection(ws_url, header=headers_ws)
        ws.send(json.dumps(execute_msg))
        print("Sent code.")

        while True:
            try:
                result = ws.recv()
                data = json.loads(result)
                if data.get("parent_header", {}).get("msg_id") == msg_id:
                    msg_type = data.get("msg_type", "")
                    content = data.get("content", {})
                    if msg_type == "stream":
                        print(content.get("text", ""), end="")
                        code_ran = 1
                        ws.close()
                    elif msg_type == "error":
                        print("\nError:", "\n".join(content.get("traceback", [])))
                        code_ran = 0
                        ws.close()
            except Exception:
                break

        ws.close()

        return code_ran
    
    def stop_server(self):
        r = requests.delete(f"{self.endpoint}/hub/api/users/{self.user}/server", headers=self.headers)
        return self.status_code(r)
    

def main():
    t0 = time.time()
    jp_test = jupyter_test()

    status = jp_test.start_server()
    if status == 0:
        print("start_server", status)
        return 0, t0

    jp_test.wait_start()

    status, kernel_id = jp_test.start_kernel()
    if status == 0:
        print("start_kernel", status)
        return 0, t0

    status = jp_test.start_session(kernel_id=kernel_id)
    if status == 0:
        print("start_session", status)
        return 0, t0

    status = jp_test.create_websocket(kernel_id=kernel_id)
    if status == 0:
        print("create_websocket", status)
        return 0, t0
    
    status = jp_test.stop_server()
    if status == 0:
        print("stop_server", status)
        return 0, t0
    
    return 1, t0

if __name__ == "__main__":

    success, t0 = main()
    #push_e2e_result(SERVICE, success, time.time() - t0)
from locust import HttpUser, task, between
from io import BytesIO
import random
import string

#comment for testing ci
class FileStorageUser(HttpUser):    
    wait_time = between(1, 3)
    
    uploaded_files = []
    
    def on_start(self):
        self.upload_initial_file()
    
    def upload_initial_file(self):
        filename = f"initial_{self.generate_random_string(8)}.txt"
        content = self.generate_random_content(1024)  
        
        files = {"file": (filename, BytesIO(content), "text/plain")}
        response = self.client.post("/files", files=files)
        
        if response.status_code == 200:
            self.uploaded_files.append(filename)
    
    @staticmethod
    def generate_random_string(length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @staticmethod
    def generate_random_content(size_bytes):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size_bytes)).encode()
    
    @task(3)
    def upload_small_file(self):
        filename = f"file_{self.generate_random_string(10)}.txt"
        size = random.randint(1024, 10240)
        content = self.generate_random_content(size)
        
        files = {"file": (filename, BytesIO(content), "text/plain")}
        
        with self.client.post(
            "/files",
            files=files,
            catch_response=True,
            name="/files [upload_small]"
        ) as response:
            if response.status_code == 200:
                self.uploaded_files.append(filename)
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def upload_medium_file(self):
        filename = f"medium_{self.generate_random_string(10)}.dat"
        size = random.randint(102400, 512000)
        content = self.generate_random_content(size)
        
        files = {"file": (filename, BytesIO(content), "application/octet-stream")}
        
        with self.client.post(
            "/files",
            files=files,
            catch_response=True,
            name="/files [upload_medium]"
        ) as response:
            if response.status_code == 200:
                self.uploaded_files.append(filename)
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(4)
    def retrieve_file(self):
        if not self.uploaded_files:
            self.upload_initial_file()
        
        if self.uploaded_files:
            filename = random.choice(self.uploaded_files)
            
            with self.client.get(
                f"/files/{filename}",
                catch_response=True,
                name="/files/{filename} [retrieve]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to retrieve file: {response.status_code}")
    
    @task(2)
    def list_files(self):
        with self.client.get(
            "/files",
            catch_response=True,
            name="/files [list]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "files" in data and "count" in data:
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(5)
    def health_check(self):
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Server reported unhealthy status")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(3)
    def get_metrics(self):
        with self.client.get(
            "/metrics",
            catch_response=True,
            name="/metrics"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "files_stored_total",
                    "files_current",
                    "total_storage_bytes"
                ]
                if all(field in data for field in required_fields):
                    response.success()
                else:
                    response.failure("Missing required metrics fields")
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(1)
    def retrieve_nonexistent_file(self):
        fake_filename = f"nonexistent_{self.generate_random_string(10)}.txt"
        
        with self.client.get(
            f"/files/{fake_filename}",
            catch_response=True,
            name="/files/{filename} [404]"
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got: {response.status_code}")


class HeavyLoadUser(HttpUser):
    wait_time = between(2, 5)
    
    @task(1)
    def upload_large_file(self):
        filename = f"large_{FileStorageUser.generate_random_string(10)}.bin"
        size = random.randint(1048576, 5242880)
        content = FileStorageUser.generate_random_content(size)
        
        files = {"file": (filename, BytesIO(content), "application/octet-stream")}
        
        with self.client.post(
            "/files",
            files=files,
            catch_response=True,
            name="/files [upload_large]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def check_metrics(self):
        self.client.get("/metrics", name="/metrics [heavy_user]")
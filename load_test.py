from locust import HttpUser, task, between
import json
import random


class RAGbotUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up authentication token"""
        self.token = "test-token-123"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def ask_question(self):
        """Test question answering endpoint"""
        questions = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What are the benefits of deep learning?",
            "Explain neural networks",
            "What is natural language processing?",
            "How do transformers work?",
            "What is computer vision?",
            "Explain reinforcement learning"
        ]
        
        payload = {
            "question": random.choice(questions),
            "question_type": "factual",
            "top_k": 5,
            "similarity_threshold": 0.7,
            "include_sources": True,
            "max_answer_length": 300,
            "temperature": 0.7
        }
        
        self.client.post(
            "/ask",
            json=payload,
            headers=self.headers,
            name="/ask - factual question"
        )
    
    @task(2)
    def chat_interaction(self):
        """Test chat endpoint"""
        messages = [
            "Hello, how can you help me?",
            "What is the difference between AI and ML?",
            "Can you explain deep learning?",
            "What are the latest trends in AI?",
            "How do I get started with machine learning?"
        ]
        
        payload = {
            "messages": [
                {"role": "user", "content": random.choice(messages)}
            ],
            "conversation_id": f"conv_{random.randint(1000, 9999)}",
            "top_k": 3,
            "include_context": True
        }
        
        self.client.post(
            "/chat",
            json=payload,
            headers=self.headers,
            name="/chat - user message"
        )
    
    @task(1)
    def search_documents(self):
        """Test search endpoint"""
        queries = [
            "machine learning algorithms",
            "neural network architecture",
            "deep learning frameworks",
            "AI applications",
            "data science techniques"
        ]
        
        payload = {
            "query": random.choice(queries),
            "top_k": 10,
            "filters": {}
        }
        
        self.client.post(
            "/search",
            json=payload,
            headers=self.headers,
            name="/search - document search"
        )
    
    @task(1)
    def batch_questions(self):
        """Test batch processing endpoint"""
        batch_questions = [
            {"question": "What is AI?", "question_type": "factual"},
            {"question": "Compare ML vs DL", "question_type": "comparative"},
            {"question": "Summarize AI benefits", "question_type": "summarization"}
        ]
        
        payload = {
            "questions": batch_questions,
            "batch_id": f"batch_{random.randint(1000, 9999)}"
        }
        
        self.client.post(
            "/batch",
            json=payload,
            headers=self.headers,
            name="/batch - multiple questions"
        )
    
    @task(1)
    def get_health(self):
        """Test health check endpoint"""
        self.client.get("/health", name="/health")
    
    @task(1)
    def get_metrics(self):
        """Test metrics endpoint"""
        self.client.get("/metrics", name="/metrics")
    
    @task(1)
    def get_stats(self):
        """Test stats endpoint"""
        self.client.get("/stats", headers=self.headers, name="/stats")


class RAGbotAdminUser(HttpUser):
    wait_time = between(5, 10)
    weight = 1  # Lower weight for admin operations
    
    def on_start(self):
        """Set up authentication token"""
        self.token = "admin-token-456"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(1)
    def list_documents(self):
        """Test document listing"""
        self.client.get("/documents", headers=self.headers, name="/documents - list")
    
    @task(1)
    def clear_cache(self):
        """Test cache clearing"""
        self.client.post("/cache/clear", headers=self.headers, name="/cache/clear")
    
    @task(1)
    def upload_document(self):
        """Test document upload (simulated)"""
        # Create a simple text file for upload
        files = {
            'file': ('test_document.txt', 'This is a test document for load testing.', 'text/plain')
        }
        data = {
            'metadata': json.dumps({"category": "test", "author": "load_tester"})
        }
        
        self.client.post(
            "/upload",
            files=files,
            data=data,
            headers=self.headers,
            name="/upload - document"
        )


# Custom events for monitoring
from locust import events

@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """Custom request handler for detailed monitoring"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    else:
        print(f"Request successful: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when a test is starting"""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when a test is ending"""
    print("Load test completed!") 
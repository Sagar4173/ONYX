# 📊 Performance Guide

## Overview

This guide provides comprehensive information about ONYX Platform performance characteristics, optimization strategies, and best practices for achieving optimal performance in various deployment scenarios.

---

## 🎯 Performance Metrics

### Key Performance Indicators (KPIs)

**Scan Performance:**

- **Average Scan Time**: 5-15 minutes per repository (depending on size)
- **Concurrent Scans**: Up to 10 simultaneous scans (configurable)
- **Repository Size Support**: Up to 1GB repositories efficiently
- **Throughput**: 100+ scans per day per instance

**API Performance:**

- **Response Time**: < 200ms for report queries
- **Request Throughput**: 1000+ requests per minute
- **WebSocket Latency**: < 50ms for real-time updates
- **Database Queries**: < 100ms average query time

**Resource Utilization:**

- **Memory Usage**: 2-4GB typical, 8GB peak during large scans
- **CPU Usage**: 20-40% average, 80% peak during scanning
- **Disk I/O**: Primarily during repository cloning and analysis
- **Network Usage**: Dependent on repository size and AI API calls

### Performance Benchmarks

**Small Repository (< 10MB, < 1000 files):**

```
Scan Duration: 2-5 minutes
Memory Usage: 512MB - 1GB
CPU Usage: 20-40%
AI Analysis: 30-60 seconds
```

**Medium Repository (10-100MB, 1000-10000 files):**

```
Scan Duration: 5-15 minutes
Memory Usage: 1-2GB
CPU Usage: 40-60%
AI Analysis: 1-3 minutes
```

**Large Repository (100MB-1GB, 10000+ files):**

```
Scan Duration: 15-45 minutes
Memory Usage: 2-4GB
CPU Usage: 60-80%
AI Analysis: 3-8 minutes
```

---

## ⚡ Performance Optimization

### Backend Optimization

**1. Scanner Configuration**

```python
# Optimized scanner settings in config.py
SCANNER_CONFIG = {
    "semgrep": {
        "max_memory": "2GB",
        "timeout": 600,  # 10 minutes
        "rules": "auto",  # Use curated rule sets
        "exclude_paths": [
            "node_modules/",
            "vendor/",
            "*.min.js",
            "*.bundle.js",
            "test/",
            "tests/"
        ]
    },
    "trivy": {
        "timeout": 300,  # 5 minutes
        "cache_backend": "redis",
        "parallel": 4,
        "skip_update": False
    },
    "gitleaks": {
        "timeout": 180,  # 3 minutes
        "baseline": True,  # Use baseline to reduce false positives
        "redact": True
    }
}
```

**2. Database Optimization**

```javascript
// MongoDB index optimization
db.reports.createIndex({ created_at: -1 });
db.reports.createIndex({ project_name: 1, status: 1 });
db.reports.createIndex({ "git_metadata.repository_url": 1 });
db.reports.createIndex({ "scan_results.findings.severity": 1 });
db.reports.createIndex({ total_findings: -1 });

// Compound indexes for complex queries
db.reports.createIndex({
  project_name: 1,
  created_at: -1,
  status: 1,
});

// TTL index for automatic cleanup of old data
db.reports.createIndex(
  { created_at: 1 },
  { expireAfterSeconds: 7776000 } // 90 days
);
```

**3. Async Processing Optimization**

```python
# Optimized async configuration
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedScanner:
    def __init__(self):
        self.max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    async def run_scanners_parallel(self, scanners, repo_path):
        """Run scanners in parallel with optimal resource allocation"""
        # Separate CPU-intensive and I/O-intensive scanners
        cpu_intensive = ['semgrep', 'bandit']
        io_intensive = ['trivy', 'gitleaks', 'safety']

        # Run CPU-intensive scanners with limited concurrency
        cpu_semaphore = asyncio.Semaphore(2)
        # Run I/O-intensive scanners with higher concurrency
        io_semaphore = asyncio.Semaphore(5)

        tasks = []
        for scanner_name, scanner in scanners.items():
            if scanner_name in cpu_intensive:
                semaphore = cpu_semaphore
            else:
                semaphore = io_semaphore

            task = self._run_scanner_with_semaphore(
                scanner, repo_path, semaphore
            )
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)
```

**4. Memory Management**

```python
# Memory-efficient repository processing
class MemoryOptimizedProcessor:
    def __init__(self):
        self.chunk_size = 1000  # Process files in chunks
        self.max_file_size = 10 * 1024 * 1024  # 10MB max file size

    async def process_repository(self, repo_path):
        """Process repository with memory constraints"""
        files = self.get_scannable_files(repo_path)

        # Process files in chunks to manage memory
        for chunk in self.chunk_files(files, self.chunk_size):
            await self.process_file_chunk(chunk)
            # Force garbage collection after each chunk
            gc.collect()

    def get_scannable_files(self, repo_path):
        """Get files to scan with size filtering"""
        scannable_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip large directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) <= self.max_file_size:
                    scannable_files.append(file_path)

        return scannable_files
```

### Frontend Optimization

**1. React Performance Optimization**

```jsx
// Optimized component with React.memo and useMemo
import React, { memo, useMemo, useCallback } from "react";

const ReportsList = memo(({ reports, filters, onFilterChange }) => {
  // Memoize filtered results
  const filteredReports = useMemo(() => {
    return reports.filter((report) => {
      if (filters.severity && report.severity !== filters.severity)
        return false;
      if (filters.status && report.status !== filters.status) return false;
      if (filters.project && !report.project_name.includes(filters.project))
        return false;
      return true;
    });
  }, [reports, filters]);

  // Memoize event handlers
  const handleSeverityFilter = useCallback(
    (severity) => {
      onFilterChange({ ...filters, severity });
    },
    [filters, onFilterChange]
  );

  return (
    <div className="reports-list">
      {filteredReports.map((report) => (
        <ReportCard key={report.id} report={report} />
      ))}
    </div>
  );
});

// Virtualized list for large datasets
import { FixedSizeList as List } from "react-window";

const VirtualizedReportsList = ({ reports }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <ReportCard report={reports[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={reports.length}
      itemSize={120}
      itemData={reports}
    >
      {Row}
    </List>
  );
};
```

**2. Code Splitting and Lazy Loading**

```jsx
// Route-based code splitting
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("./components/Dashboard"));
const Reports = lazy(() => import("./components/Reports"));
const Settings = lazy(() => import("./components/Settings"));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}

// Component-level lazy loading
const LazyChart = lazy(() =>
  import("./Chart").then((module) => ({ default: module.Chart }))
);
```

**3. Data Fetching Optimization**

```jsx
// Optimized data fetching with React Query
import { useQuery, useInfiniteQuery } from "@tanstack/react-query";

// Cached queries with stale-while-revalidate
const useReports = (filters) => {
  return useQuery({
    queryKey: ["reports", filters],
    queryFn: () => fetchReports(filters),
    staleTime: 30000, // 30 seconds
    cacheTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

// Infinite scrolling for large datasets
const useInfiniteReports = (filters) => {
  return useInfiniteQuery({
    queryKey: ["reports", "infinite", filters],
    queryFn: ({ pageParam = 1 }) =>
      fetchReports({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage, pages) => {
      return lastPage.hasMore ? pages.length + 1 : undefined;
    },
  });
};
```

### Database Performance

**1. Query Optimization**

```javascript
// Optimized aggregation pipelines
// Get vulnerability trends
db.reports.aggregate([
  {
    $match: {
      created_at: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
    },
  },
  {
    $group: {
      _id: {
        $dateToString: { format: "%Y-%m-%d", date: "$created_at" },
      },
      total_findings: { $sum: "$total_findings" },
      critical: { $sum: "$findings_by_severity.critical" },
      high: { $sum: "$findings_by_severity.high" },
    },
  },
  { $sort: { _id: 1 } },
]);

// Efficient project statistics
db.reports.aggregate([
  {
    $group: {
      _id: "$project_name",
      latest_scan: { $max: "$created_at" },
      total_scans: { $sum: 1 },
      avg_findings: { $avg: "$total_findings" },
      total_critical: { $sum: "$findings_by_severity.critical" },
    },
  },
  { $sort: { total_critical: -1 } },
]);
```

**2. Connection Pool Optimization**

```python
# Optimized MongoDB connection
from motor.motor_asyncio import AsyncIOMotorClient

class DatabaseManager:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            MONGODB_URL,
            maxPoolSize=50,  # Maximum connections
            minPoolSize=10,  # Minimum connections
            maxIdleTimeMS=30000,  # 30 seconds
            waitQueueTimeoutMS=5000,  # 5 seconds
            serverSelectionTimeoutMS=3000,  # 3 seconds
        )
        self.db = self.client[DATABASE_NAME]

    async def close(self):
        self.client.close()
```

---

## 🖥️ System Resource Optimization

### Memory Management

**1. Container Memory Limits**

```yaml
# docker-compose.yml optimizations
version: "3.8"

services:
  backend:
    image: onyx-backend:latest
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
        reservations:
          memory: 2G
          cpus: "1.0"
    environment:
      - PYTHONMALLOC=malloc
      - MALLOC_ARENA_MAX=2
    sysctls:
      - net.core.somaxconn=1024
```

**2. Python Memory Optimization**

```python
# Memory-efficient scanning
import gc
import psutil
import os

class ResourceManager:
    def __init__(self, max_memory_mb=3072):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())

    def check_memory_usage(self):
        """Check current memory usage"""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        return memory_mb

    def should_cleanup(self):
        """Determine if memory cleanup is needed"""
        return self.check_memory_usage() > self.max_memory_mb * 0.8

    def cleanup_memory(self):
        """Force garbage collection and memory cleanup"""
        gc.collect()
        if hasattr(gc, 'set_debug'):
            gc.set_debug(0)  # Disable debug mode to reduce overhead
```

### CPU Optimization

**1. Process Pool Configuration**

```python
# CPU-optimized scanner execution
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

class CPUOptimizedScanner:
    def __init__(self):
        # Use 75% of available CPU cores
        self.max_workers = max(1, int(mp.cpu_count() * 0.75))

    async def run_cpu_intensive_scans(self, scanners, repo_path):
        """Run CPU-intensive scans with process pools"""
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            tasks = []
            for scanner_name, scanner_config in scanners.items():
                if scanner_name in ['semgrep', 'bandit']:
                    task = loop.run_in_executor(
                        executor,
                        self.run_scanner_sync,
                        scanner_name,
                        repo_path,
                        scanner_config
                    )
                    tasks.append(task)

            return await asyncio.gather(*tasks)
```

**2. I/O Optimization**

```python
# Async I/O optimization
import aiofiles
import aiohttp

class IOOptimizedProcessor:
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=300)

    async def download_repository(self, repo_url, local_path):
        """Optimized repository cloning"""
        # Use shallow clone for faster downloads
        clone_cmd = [
            'git', 'clone',
            '--depth', '1',  # Shallow clone
            '--single-branch',  # Only current branch
            '--no-tags',  # Skip tags
            repo_url, local_path
        ]

        process = await asyncio.create_subprocess_exec(
            *clone_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()
        return process.returncode == 0

    async def read_file_async(self, file_path):
        """Async file reading"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

**1. Load Balancer Configuration**

```nginx
# nginx.conf for load balancing
upstream backend_servers {
    least_conn;  # Use least connections algorithm
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;

    location / {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Connection pooling
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        # Buffer optimization
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

**2. Kubernetes Horizontal Pod Autoscaler**

```yaml
# hpa.yml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: onyx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: onyx-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### Vertical Scaling

**1. Dynamic Resource Adjustment**

```python
# Dynamic resource allocation based on load
import psutil
import asyncio

class DynamicResourceManager:
    def __init__(self):
        self.current_scan_count = 0
        self.max_concurrent_scans = 10

    async def adjust_resources(self):
        """Dynamically adjust resource allocation"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        # Reduce concurrent scans if system is under pressure
        if cpu_percent > 80 or memory_percent > 85:
            self.max_concurrent_scans = max(2, self.max_concurrent_scans - 1)
        elif cpu_percent < 50 and memory_percent < 60:
            self.max_concurrent_scans = min(20, self.max_concurrent_scans + 1)

        await asyncio.sleep(30)  # Check every 30 seconds
```

---

## 🔧 Performance Monitoring

### Application Performance Monitoring (APM)

**1. Custom Metrics Collection**

```python
# Performance metrics collection
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PerformanceMetrics:
    scan_duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    ai_analysis_duration: float
    findings_count: int

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []

    async def measure_scan_performance(self, scan_func, *args, **kwargs):
        """Measure scan performance metrics"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Execute scan
        result = await scan_func(*args, **kwargs)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent()

        metrics = PerformanceMetrics(
            scan_duration=end_time - start_time,
            memory_usage_mb=end_memory - start_memory,
            cpu_usage_percent=cpu_percent,
            ai_analysis_duration=result.get('ai_analysis_duration', 0),
            findings_count=result.get('total_findings', 0)
        )

        self.metrics.append(metrics)
        await self.log_metrics(metrics)

        return result

    async def log_metrics(self, metrics: PerformanceMetrics):
        """Log performance metrics"""
        logging.info(f"Scan Performance: "
                    f"Duration: {metrics.scan_duration:.2f}s, "
                    f"Memory: {metrics.memory_usage_mb:.2f}MB, "
                    f"CPU: {metrics.cpu_usage_percent:.1f}%, "
                    f"Findings: {metrics.findings_count}")
```

**2. Prometheus Metrics Integration**

```python
# Prometheus metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
SCAN_DURATION = Histogram('scan_duration_seconds', 'Scan duration in seconds', ['scanner_type'])
SCAN_COUNTER = Counter('scans_total', 'Total number of scans', ['status'])
ACTIVE_SCANS = Gauge('active_scans', 'Number of currently active scans')
MEMORY_USAGE = Gauge('memory_usage_mb', 'Current memory usage in MB')

class PrometheusMonitor:
    def __init__(self):
        start_http_server(8001)  # Metrics endpoint on port 8001

    def record_scan_start(self, scanner_type: str):
        ACTIVE_SCANS.inc()
        return time.time()

    def record_scan_complete(self, scanner_type: str, start_time: float, status: str):
        duration = time.time() - start_time
        SCAN_DURATION.labels(scanner_type=scanner_type).observe(duration)
        SCAN_COUNTER.labels(status=status).inc()
        ACTIVE_SCANS.dec()

    def update_memory_usage(self):
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        MEMORY_USAGE.set(memory_mb)
```

### Database Performance Monitoring

**1. Query Performance Analysis**

```javascript
// MongoDB query profiling
// Enable profiling for slow queries
db.setProfilingLevel(2, { slowms: 100 });

// Analyze slow queries
db.system.profile.find().limit(5).sort({ ts: -1 }).pretty();

// Create explain plans for optimization
db.reports.find({ project_name: "test" }).explain("executionStats");
```

**2. Database Metrics Collection**

```python
# Database performance monitoring
class DatabaseMonitor:
    def __init__(self, db):
        self.db = db

    async def collect_metrics(self):
        """Collect database performance metrics"""
        # Connection pool stats
        pool_stats = self.db.client.get_default_database().command("connPoolStats")

        # Operation stats
        server_status = self.db.client.get_default_database().command("serverStatus")

        # Collection stats
        collection_stats = {}
        for collection_name in ['reports', 'users', 'projects']:
            stats = self.db[collection_name].estimated_document_count()
            collection_stats[collection_name] = stats

        return {
            'pool_stats': pool_stats,
            'server_status': server_status,
            'collection_stats': collection_stats
        }
```

---

## 🎛️ Performance Tuning

### Scanner-Specific Optimizations

**1. Semgrep Optimization**

```yaml
# .semgrep.yml - Optimized Semgrep configuration
rules:
  - id: optimized-semgrep-config
    patterns:
      - pattern-inside: |
          def $FUNC(...):
            ...
    message: Custom rule
    languages: [python]
    severity: INFO

# Performance settings
options:
  max_memory: 2048 # MB
  max_time: 600 # seconds

# Exclude patterns for better performance
exclude:
  - "*.min.js"
  - "*.bundle.js"
  - "node_modules/*"
  - "vendor/*"
  - "third_party/*"
  - "*.test.js"
  - "test/*"
  - "tests/*"
```

**2. Trivy Optimization**

```yaml
# trivy-config.yaml
cache:
  redis:
    addr: "redis:6379"

vulnerability:
  type: "os,library"

scan:
  parallel: 4
  skip-update: false

format: json
timeout: 5m

# Ignore files
.trivyignore: |
  *.log
  *.tmp
  node_modules/
  vendor/
```

### AI Analysis Optimization

**1. Token Usage Optimization**

```python
# Optimized AI prompt engineering
class OptimizedAIProcessor:
    def __init__(self):
        self.max_tokens = 2000
        self.temperature = 0.1  # Lower temperature for consistent results

    def create_optimized_prompt(self, findings: List[Dict]) -> str:
        """Create token-efficient prompts"""
        # Prioritize critical and high severity findings
        critical_findings = [f for f in findings if f['severity'] in ['critical', 'high']]

        # Limit findings to fit within token limits
        if len(critical_findings) > 10:
            critical_findings = critical_findings[:10]

        prompt = f"""
        Analyze these {len(critical_findings)} security findings:

        {self.format_findings_concisely(critical_findings)}

        Provide:
        1. Risk assessment (1-2 sentences)
        2. Top 3 priority items
        3. Quick remediation steps

        Keep response under 500 words.
        """

        return prompt

    def format_findings_concisely(self, findings: List[Dict]) -> str:
        """Format findings in a token-efficient manner"""
        formatted = []
        for i, finding in enumerate(findings, 1):
            formatted.append(
                f"{i}. {finding['title']} "
                f"({finding['severity']}) in {finding['file_path']}:{finding['line_number']}"
            )
        return "\n".join(formatted)
```

**2. Caching Strategy**

```python
# AI response caching
import hashlib
import pickle
from typing import Optional

class AIResponseCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 86400  # 24 hours

    def generate_cache_key(self, findings: List[Dict]) -> str:
        """Generate cache key from findings"""
        # Create deterministic hash from findings
        findings_str = str(sorted(findings, key=lambda x: x.get('id', '')))
        return f"ai_analysis:{hashlib.md5(findings_str.encode()).hexdigest()}"

    async def get_cached_analysis(self, findings: List[Dict]) -> Optional[Dict]:
        """Get cached AI analysis"""
        cache_key = self.generate_cache_key(findings)
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            return pickle.loads(cached_data)
        return None

    async def cache_analysis(self, findings: List[Dict], analysis: Dict):
        """Cache AI analysis result"""
        cache_key = self.generate_cache_key(findings)
        serialized_data = pickle.dumps(analysis)
        await self.redis.setex(cache_key, self.cache_ttl, serialized_data)
```

---

## 📊 Performance Testing

### Load Testing

**1. API Load Testing with Locust**

```python
# locustfile.py
from locust import HttpUser, task, between
import random

class ONYXUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get auth token"""
        response = self.client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_reports(self):
        """Test report retrieval"""
        self.client.get("/api/reports", headers=self.headers)

    @task(1)
    def submit_scan(self):
        """Test scan submission"""
        self.client.post("/webhook/scan",
                        json={
                            "repository_url": f"https://github.com/test/repo{random.randint(1,100)}.git",
                            "branch": "main"
                        },
                        headers=self.headers)

    @task(2)
    def get_specific_report(self):
        """Test specific report retrieval"""
        # Get a random report ID (in real test, use actual IDs)
        report_id = f"scan-{random.randint(1000, 9999)}"
        self.client.get(f"/api/reports/{report_id}", headers=self.headers)

# Run test: locust -f locustfile.py --host=http://localhost:8000
```

**2. Database Performance Testing**

```python
# db_performance_test.py
import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient

class DatabasePerformanceTest:
    def __init__(self):
        self.client = AsyncIOMotorClient("mongodb://localhost:27017")
        self.db = self.client.test_db

    async def test_write_performance(self, num_documents=1000):
        """Test write performance"""
        start_time = time.time()

        documents = [
            {
                "scan_id": f"scan_{i}",
                "project_name": f"project_{i % 10}",
                "total_findings": i % 100,
                "created_at": time.time()
            }
            for i in range(num_documents)
        ]

        await self.db.reports.insert_many(documents)

        duration = time.time() - start_time
        print(f"Inserted {num_documents} documents in {duration:.2f}s")
        print(f"Rate: {num_documents/duration:.2f} docs/sec")

    async def test_read_performance(self, num_queries=100):
        """Test read performance"""
        start_time = time.time()

        for i in range(num_queries):
            project_name = f"project_{i % 10}"
            result = await self.db.reports.find(
                {"project_name": project_name}
            ).to_list(length=10)

        duration = time.time() - start_time
        print(f"Executed {num_queries} queries in {duration:.2f}s")
        print(f"Rate: {num_queries/duration:.2f} queries/sec")

# Run tests
async def main():
    test = DatabasePerformanceTest()
    await test.test_write_performance()
    await test.test_read_performance()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛠️ Troubleshooting Performance Issues

### Common Performance Problems

**1. Slow Scan Times**

_Symptoms:_ Scans taking longer than expected
_Diagnosis:_

```bash
# Check system resources during scan
htop
iotop
df -h

# Check individual scanner performance
time semgrep --config=auto /path/to/repo
time trivy fs /path/to/repo
```

_Solutions:_

- Optimize exclude patterns
- Increase system resources
- Use scanner-specific optimizations
- Implement file size limits

**2. High Memory Usage**

_Symptoms:_ Memory usage continuously increasing
_Diagnosis:_

```python
# Memory profiling
import tracemalloc

tracemalloc.start()

# Run your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

_Solutions:_

- Implement garbage collection
- Process files in chunks
- Set memory limits for containers
- Use memory-efficient data structures

**3. Database Performance Issues**

_Symptoms:_ Slow query responses
_Diagnosis:_

```javascript
// MongoDB query analysis
db.reports.find({ project_name: "test" }).explain("executionStats");

// Check index usage
db.reports.getIndexes();
```

_Solutions:_

- Add appropriate indexes
- Optimize aggregation pipelines
- Implement query result caching
- Use read replicas for read-heavy workloads

---

## 📋 Performance Checklist

### Pre-deployment Performance Optimization

- [ ] **Scanner Configuration**

  - [ ] Exclude patterns configured
  - [ ] Timeout limits set appropriately
  - [ ] Memory limits configured
  - [ ] Parallel execution optimized

- [ ] **Database Optimization**

  - [ ] Indexes created for common queries
  - [ ] Connection pool configured
  - [ ] TTL indexes for data cleanup
  - [ ] Query performance tested

- [ ] **Application Optimization**

  - [ ] Async/await patterns implemented
  - [ ] Memory management strategies in place
  - [ ] Caching layers configured
  - [ ] Resource monitoring enabled

- [ ] **Infrastructure Optimization**
  - [ ] Container resource limits set
  - [ ] Load balancing configured
  - [ ] Auto-scaling policies defined
  - [ ] Monitoring and alerting set up

### Ongoing Performance Monitoring

- [ ] **Regular Performance Reviews**

  - [ ] Weekly performance metrics analysis
  - [ ] Monthly capacity planning reviews
  - [ ] Quarterly performance optimization sprints
  - [ ] Annual architecture reviews

- [ ] **Automated Monitoring**
  - [ ] Performance alerts configured
  - [ ] Resource utilization dashboards
  - [ ] SLA monitoring in place
  - [ ] Automated performance testing

---

This performance guide provides a comprehensive foundation for optimizing ONYX Platform. Regular monitoring and optimization based on actual usage patterns will ensure continued high performance as your deployment scales.

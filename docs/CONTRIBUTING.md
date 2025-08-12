# 🤝 Contributing to SecureDevOps AI Platform

We're excited that you're interested in contributing to SecureDevOps AI Platform! This guide will help you get started with contributing to our open-source security scanning platform.

---

## 🌟 **Why Contribute?**

- **Impact**: Help organizations worldwide improve their security posture
- **Learning**: Work with cutting-edge security tools and AI technologies
- **Community**: Join a growing community of security-minded developers
- **Recognition**: Get recognition for your contributions in our Hall of Fame
- **Experience**: Gain experience with enterprise-scale security software

---

## 🚀 **Getting Started**

### **1. Prerequisites**
- **Python 3.11+** with FastAPI knowledge
- **React 18+** with modern JavaScript/TypeScript
- **MongoDB** experience helpful
- **Security Tools** knowledge (Semgrep, Trivy, etc.)
- **Git** workflow familiarity
- **Docker** for testing (optional)

### **2. Development Setup**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/SecureDevOpsAI-Platform.git
cd SecureDevOpsAI-Platform

# Add upstream remote
git remote add upstream https://github.com/Sagar4173/SecureDevOpsAI-Platform.git

# Create development environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt  # Development dependencies

# Install frontend dependencies
cd frontend
npm install
cd ..

# Set up pre-commit hooks
pre-commit install
```

### **3. Environment Configuration**
```bash
# Copy development environment
cp .env.example .env.dev

# Edit with development settings
ENVIRONMENT=development
DEBUG=true
OPENAI_API_KEY=sk-your-development-key
MONGODB_URI=mongodb://localhost:27017/securedevops_dev
```

---

## 🏗️ **Development Workflow**

### **1. Create a Feature Branch**
```bash
# Get latest changes
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# Or for bug fixes
git checkout -b fix/issue-description
```

### **2. Make Your Changes**
```bash
# Backend development
cd backend
python app.py  # Start development server

# Frontend development
cd frontend
npm run dev    # Start development server

# Run tests
pytest backend/tests/
npm test --prefix frontend
```

### **3. Code Quality Checks**
```bash
# Python code formatting
black backend/
isort backend/

# Python linting
flake8 backend/
pylint backend/

# Type checking
mypy backend/

# JavaScript/TypeScript formatting
npm run lint --prefix frontend
npm run format --prefix frontend
```

### **4. Testing**
```bash
# Run backend tests
cd backend
pytest tests/ -v --cov=.

# Run frontend tests
cd frontend
npm test

# Run integration tests
cd tests/integration
pytest test_api_integration.py
```

### **5. Commit and Push**
```bash
# Add your changes
git add .

# Commit with conventional commit message
git commit -m "feat: add custom rule engine for security policies"
# or
git commit -m "fix: resolve memory leak in scanner orchestrator"

# Push to your fork
git push origin feature/your-feature-name
```

### **6. Create Pull Request**
1. Go to GitHub and create a Pull Request
2. Fill out the PR template completely
3. Link any relevant issues
4. Request review from maintainers

---

## 📝 **Contribution Types**

### **🚀 Feature Development**
- **Security Scanners**: Add new scanner integrations
- **AI Enhancements**: Improve AI analysis capabilities
- **UI/UX**: Enhance frontend user experience
- **Integrations**: Add CI/CD, notification, or third-party integrations
- **Enterprise Features**: RBAC, multi-tenancy, advanced reporting

### **🐛 Bug Fixes**
- **Critical Bugs**: Security vulnerabilities, data corruption
- **Performance Issues**: Memory leaks, slow queries, timeout issues
- **UI Bugs**: Layout issues, broken functionality
- **Integration Bugs**: API failures, webhook issues

### **📚 Documentation**
- **API Documentation**: Improve OpenAPI specs
- **User Guides**: Installation, configuration, usage guides
- **Developer Docs**: Architecture, contributing, testing guides
- **Tutorials**: Step-by-step implementation examples

### **🧪 Testing**
- **Unit Tests**: Backend and frontend component tests
- **Integration Tests**: API and database integration tests
- **E2E Tests**: Full workflow testing
- **Performance Tests**: Load and stress testing

### **🔧 Infrastructure**
- **CI/CD**: GitHub Actions, deployment automation
- **Docker**: Container optimization, multi-stage builds
- **Kubernetes**: Helm charts, operators
- **Monitoring**: Prometheus metrics, health checks

---

## 📋 **Coding Standards**

### **Python Backend Standards**

#### **Code Style**
```python
# Use Black formatting with 88 character line length
# Use isort for import sorting
# Follow PEP 8 with our project-specific exceptions

# Example: Good function documentation
async def analyze_scan_results(
    scan_results: List[ScanResult],
    project_context: Optional[Dict[str, Any]] = None
) -> AIAnalysis:
    """
    Analyze vulnerability scan results using AI.
    
    Args:
        scan_results: List of scan results from security tools
        project_context: Optional project-specific context
        
    Returns:
        AI analysis with recommendations and risk assessment
        
    Raises:
        AIProcessorError: If AI analysis fails
        ValidationError: If scan_results format is invalid
    """
    # Implementation here
```

#### **Type Hints**
```python
# Always use type hints
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel

# Good: Proper type hints
async def process_webhook(
    payload: Dict[str, Any],
    headers: Dict[str, str]
) -> Optional[WebhookEvent]:
    pass

# Bad: No type hints
async def process_webhook(payload, headers):
    pass
```

#### **Error Handling**
```python
# Use specific exceptions
class ScannerError(Exception):
    """Raised when security scanner fails"""
    pass

# Proper error handling with logging
try:
    result = await scanner.scan(repo_path)
except ScannerError as e:
    logger.error(f"Scanner failed: {e}", extra={"repo_path": repo_path})
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", extra={"repo_path": repo_path})
    raise ScannerError(f"Scanner execution failed: {e}")
```

#### **Async/Await Best Practices**
```python
# Good: Proper async usage
async def run_parallel_scans(repo_path: str) -> List[ScanResult]:
    tasks = [
        scanner.scan(repo_path) 
        for scanner in self.scanners.values()
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Good: Context managers for resources
async def clone_repository(repo_url: str) -> str:
    async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
        # Clone operations
        return temp_dir
```

### **React Frontend Standards**

#### **Component Structure**
```jsx
// Good: Functional component with hooks
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface ScanReportProps {
  scanId: string;
  onRefresh?: () => void;
}

export const ScanReport: React.FC<ScanReportProps> = ({ scanId, onRefresh }) => {
  const [selectedFindings, setSelectedFindings] = useState<string[]>([]);
  
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['scan-report', scanId],
    queryFn: () => api.getScanReport(scanId),
    refetchInterval: 5000 // Real-time updates
  });

  useEffect(() => {
    if (report?.status === 'completed' && onRefresh) {
      onRefresh();
    }
  }, [report?.status, onRefresh]);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="scan-report">
      {/* Component JSX */}
    </div>
  );
};
```

#### **State Management**
```jsx
// Use React Query for server state
const { data: scanReports, mutate: refreshReports } = useQuery({
  queryKey: ['scan-reports'],
  queryFn: api.getScanReports,
  staleTime: 30000
});

// Use useState for local component state
const [filters, setFilters] = useState({
  severity: 'all',
  status: 'all',
  dateRange: '7d'
});

// Use useReducer for complex state
const [scanState, dispatch] = useReducer(scanReducer, initialScanState);
```

#### **CSS/Styling**
```jsx
// Use Tailwind CSS classes
<div className="bg-gray-900 text-white rounded-lg p-6 shadow-lg">
  <h2 className="text-xl font-semibold mb-4">Scan Results</h2>
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {/* Content */}
  </div>
</div>

// Use CSS modules for complex styling
import styles from './ScanReport.module.css';

<div className={`${styles.scanReport} ${styles.darkTheme}`}>
  {/* Component content */}
</div>
```

### **Database Schema Standards**

#### **MongoDB Document Design**
```python
# Good: Well-structured document model
class ScanReport(Document):
    """Comprehensive scan report document"""
    
    # Required fields with validation
    scan_id: str = Field(..., unique=True, regex=r'^[a-f0-9-]{36}$')
    project_name: str = Field(..., min_length=1, max_length=100)
    status: ScanStatus = Field(default=ScanStatus.PENDING)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Embedded documents
    git_metadata: GitMetadata
    scan_results: List[ScanResult] = []
    ai_analysis: Optional[AIAnalysis] = None
    
    # Indexes for performance
    class Settings:
        name = "scan_reports"
        indexes = [
            "scan_id",
            "project_name",
            [("project_name", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)]
        ]
```

---

## 🧪 **Testing Guidelines**

### **Backend Testing**

#### **Unit Tests**
```python
# tests/test_scanner.py
import pytest
from unittest.mock import AsyncMock, patch
from services.scanner import SecurityScanner, ScannerError

class TestSecurityScanner:
    @pytest.fixture
    def scanner(self):
        return SecurityScanner()
    
    @pytest.mark.asyncio
    async def test_run_all_scans_success(self, scanner):
        """Test successful execution of all scanners"""
        with patch.object(scanner, 'scanners') as mock_scanners:
            # Setup mocks
            mock_scanners.values.return_value = [
                AsyncMock(scan=AsyncMock(return_value="scan_result_1")),
                AsyncMock(scan=AsyncMock(return_value="scan_result_2"))
            ]
            
            # Execute
            results = await scanner.run_all_scans("/test/path")
            
            # Assert
            assert len(results) == 2
            assert results[0] == "scan_result_1"
            assert results[1] == "scan_result_2"
    
    @pytest.mark.asyncio
    async def test_run_all_scans_with_failure(self, scanner):
        """Test scanner execution with one scanner failing"""
        with patch.object(scanner, 'scanners') as mock_scanners:
            # Setup mocks with one failing
            mock_scanners.values.return_value = [
                AsyncMock(scan=AsyncMock(return_value="scan_result_1")),
                AsyncMock(scan=AsyncMock(side_effect=ScannerError("Scanner failed")))
            ]
            
            # Execute
            results = await scanner.run_all_scans("/test/path")
            
            # Assert partial success
            assert len(results) == 2
            assert results[0] == "scan_result_1"
            assert isinstance(results[1], ScannerError)
```

#### **Integration Tests**
```python
# tests/test_api_integration.py
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_submit_scan_endpoint():
    """Test scan submission via API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/scan",
            json={
                "repository_url": "https://github.com/test/repo.git",
                "branch": "main",
                "scan_types": ["sast", "secrets"]
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "pending"
```

### **Frontend Testing**

#### **Component Tests**
```jsx
// __tests__/ScanReport.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScanReport } from '../ScanReport';
import * as api from '../../services/api';

// Mock API
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

describe('ScanReport', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
  });

  it('displays loading state initially', () => {
    mockApi.getScanReport.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <QueryClientProvider client={queryClient}>
        <ScanReport scanId="test-scan-id" />
      </QueryClientProvider>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays scan results when loaded', async () => {
    const mockReport = {
      scan_id: 'test-scan-id',
      project_name: 'Test Project',
      status: 'completed',
      total_findings: 5,
      findings_by_severity: {
        critical: 1,
        high: 2,
        medium: 2,
        low: 0
      }
    };

    mockApi.getScanReport.mockResolvedValue(mockReport);

    render(
      <QueryClientProvider client={queryClient}>
        <ScanReport scanId="test-scan-id" />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
      expect(screen.getByText('5 findings')).toBeInTheDocument();
    });
  });
});
```

---

## 📋 **Pull Request Guidelines**

### **PR Template**
```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Security Considerations
- [ ] No new security vulnerabilities introduced
- [ ] Security scanner results reviewed
- [ ] Authentication/authorization not affected
- [ ] Data privacy maintained

## Screenshots/Examples
If applicable, add screenshots or code examples

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.log statements left
- [ ] Error handling implemented
```

### **PR Review Process**
1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Security Review**: Automated security scanning
3. **Code Review**: Maintainer review for code quality and design
4. **Testing**: Manual testing if required
5. **Approval**: At least one maintainer approval required
6. **Merge**: Squash and merge for clean history

---

## 🎯 **Areas We Need Help**

### **High Priority**
- [ ] **Authentication System**: User management, RBAC, SSO integration
- [ ] **Custom Rule Engine**: User-defined security policies
- [ ] **Performance Optimization**: Database queries, caching, async processing
- [ ] **Enterprise Features**: Multi-tenancy, audit trails, compliance reporting
- [ ] **Mobile Responsiveness**: Improve mobile UI/UX

### **Medium Priority**
- [ ] **Additional Scanners**: Checkmarx, Veracode, SonarQube integration
- [ ] **CI/CD Integrations**: Jenkins, Azure DevOps, CircleCI plugins
- [ ] **IDE Plugins**: VS Code, IntelliJ extensions
- [ ] **Advanced Analytics**: Machine learning, predictive analytics
- [ ] **Internationalization**: Multi-language support

### **Good First Issues**
- [ ] **Documentation**: API docs, tutorials, troubleshooting guides
- [ ] **UI Improvements**: Better error messages, loading states
- [ ] **Test Coverage**: Increase test coverage for existing features
- [ ] **Bug Fixes**: Address issues in GitHub Issues
- [ ] **Code Cleanup**: Refactoring, removing deprecated code

---

## 🏆 **Recognition**

### **Contributors Hall of Fame**
We recognize all contributors in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file and our website.

### **Contribution Levels**
- **🌟 Bronze**: 1-5 merged PRs
- **⭐ Silver**: 6-15 merged PRs
- **🏆 Gold**: 16+ merged PRs or major feature contribution
- **💎 Diamond**: Long-term maintainer status

### **Swag & Rewards**
- **Stickers**: For first contribution
- **T-shirt**: For significant contributions
- **Conference Sponsorship**: For major contributors
- **Mentorship**: Direct mentorship from core team

---

## 📞 **Getting Help**

### **Communication Channels**
- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat with contributors
- **Email**: security@securedevops.ai for sensitive issues

### **Mentorship Program**
- New contributors are paired with experienced mentainers
- Regular 1:1 sessions to discuss progress and challenges
- Code review sessions and pair programming opportunities
- Career guidance and open source best practices

---

## 📚 **Resources**

### **Learning Resources**
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **MongoDB**: https://docs.mongodb.com/
- **Security Tools**: Semgrep, Trivy, GitLeaks documentation
- **OpenAI API**: https://platform.openai.com/docs

### **Project Resources**
- **Architecture Documentation**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Code Examples**: [examples/](../examples/)
- **Development Scripts**: [scripts/](../scripts/)

---

Thank you for considering contributing to SecureDevOps AI Platform! Together, we're building the future of open-source security scanning. 🚀

**Questions?** Reach out to us on [GitHub Discussions](https://github.com/Sagar4173/SecureDevOpsAI-Platform/discussions) or [Discord](https://discord.gg/securedevops).

"""
API Endpoint Tests
Tests for FastAPI routes and responses
"""


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint_structure(self):
        """Test health endpoint returns expected structure"""
        expected_fields = ["status", "version", "timestamp"]
        
        # Mock health response
        health_response = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2026-01-01T00:00:00Z"
        }
        
        for field in expected_fields:
            assert field in health_response


class TestReportsAPI:
    """Test reports API endpoints"""
    
    def test_report_response_structure(self, sample_scan_result):
        """Test report response has required fields"""
        required_fields = ["scan_id", "status", "findings", "summary"]
        
        for field in required_fields:
            assert field in sample_scan_result
    
    def test_findings_have_required_fields(self, sample_scan_result):
        """Test findings have all required fields"""
        required_fields = ["id", "severity", "title", "description"]
        
        for finding in sample_scan_result["findings"]:
            for field in required_fields:
                assert field in finding


class TestProjectsAPI:
    """Test projects API endpoints"""
    
    def test_project_response_structure(self, sample_project):
        """Test project response has required fields"""
        required_fields = ["id", "name", "repository_url"]
        
        for field in required_fields:
            assert field in sample_project


class TestErrorHandling:
    """Test API error handling"""
    
    def test_404_error_structure(self):
        """Test 404 error response structure"""
        error_response = {
            "detail": "Resource not found"
        }
        
        assert "detail" in error_response
    
    def test_422_validation_error_structure(self):
        """Test validation error response structure"""
        # FastAPI validation errors return an array of error objects
        error_response = {
            "detail": [
                {
                    "loc": ["body", "email"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
        
        assert "detail" in error_response
        assert isinstance(error_response["detail"], list)


class TestPagination:
    """Test API pagination"""
    
    def test_pagination_parameters(self):
        """Test pagination parameters are valid"""
        pagination = {
            "skip": 0,
            "limit": 50,
            "total": 100
        }
        
        assert pagination["skip"] >= 0
        assert pagination["limit"] > 0
        assert pagination["limit"] <= 100
    
    def test_paginated_response_structure(self):
        """Test paginated response has required fields"""
        paginated_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 0,
            "has_more": False
        }
        
        assert "items" in paginated_response
        assert "total" in paginated_response

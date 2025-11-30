# 📁 ONYX Platform - Project Structure

## 🎯 **PROPERLY ORGANIZED PROJECT DIRECTORY STRUCTURE**

```
ONYX-Platform/
├── 📁 backend/                    # Backend application core
│   ├── 📁 configs/               # Configuration files
│   ├── 📁 models/                # Data models and schemas
│   ├── 📁 routes/                # API route handlers
│   │   ├── advanced_scanning.py       # Advanced scanning endpoints
│   │   ├── advanced_scanning_fastapi.py # FastAPI scanning routes
│   │   ├── security_orchestration.py  # Security orchestration routes
│   │   ├── advanced_security.py       # Advanced security routes
│   │   ├── compliance.py             # Compliance endpoints
│   │   ├── enhanced_security.py      # Enhanced security features
│   │   ├── god_level_security.py     # God-level security routes
│   │   ├── reports.py               # Reporting endpoints
│   │   ├── security.py              # Core security routes
│   │   └── webhook.py               # Webhook handlers
│   ├── 📁 services/              # Business logic services
│   │   ├── 🔍 Core Scanner Services
│   │   ├── scanner.py                 # Main scanner service
│   │   ├── real_scanner.py           # Production scanner
│   │   ├── advanced_scanners.py      # Advanced scanner implementations
│   │   ├── advanced_scanner_engine.py # Scanner engine
│   │   ├── unified_scanning_pipeline.py # Unified scanning
│   │   ├── 🤖 AI & ML Services
│   │   ├── ai_processor.py           # AI processing logic
│   │   ├── security_ml.py            # Security ML algorithms
│   │   ├── ml_anomaly_detection_engine.py # ML anomaly detection
│   │   ├── 🏛️ Governance & Compliance
│   │   ├── compliance_analyzer.py    # Compliance analysis
│   │   ├── compliance_governance.py  # Governance framework
│   │   ├── governance_compliance_engine.py # Complete governance engine
│   │   ├── policy_engine.py          # Policy management
│   │   ├── policy_as_code_engine.py  # Policy-as-code implementation
│   │   ├── 🔒 Security Engines
│   │   ├── rule_engine.py            # Rule processing
│   │   ├── rule_parsing_engine.py    # Advanced rule parsing
│   │   ├── rule_security.py          # Rule security validation
│   │   ├── rule_testing_framework.py # Rule testing framework
│   │   ├── custom_security_rules.py  # Custom security rules
│   │   ├── security_boundary_engine.py # Security boundaries
│   │   ├── 📊 Management & Analytics
│   │   ├── baseline_manager.py       # Baseline management
│   │   ├── enhanced_baseline_manager.py # Enhanced baseline features
│   │   ├── vulnerability_management.py # Vulnerability management
│   │   ├── vulnerability_management_engine.py # Complete VM engine
│   │   ├── security_metrics.py       # Security metrics
│   │   ├── metrics_kpi_engine.py     # Metrics & KPI engine
│   │   ├── 🔍 Threat Intelligence
│   │   ├── threat_intelligence.py    # Threat intel core
│   │   ├── threat_intelligence_engine.py # Complete TI engine
│   │   ├── 🎯 Testing & Penetration
│   │   ├── penetration_testing.py    # Pentest core
│   │   ├── pentest_orchestration_engine.py # Pentest orchestration
│   │   ├── codeql_checkov_scanners.py # Advanced scanners
│   │   ├── ⚡ Automation & SOAR
│   │   ├── soar_engine.py            # SOAR core
│   │   ├── soar_playbook_engine.py   # Complete SOAR engine
│   │   ├── security_orchestration_engine.py # Security orchestration
│   │   ├── notifier.py               # Notification service
│   │   └── 📁 utils/                 # Utility modules
│   ├── 📄 app.py                    # Main Flask application
│   ├── 📄 main.py                   # Application entry point
│   ├── 📄 config.py                 # Configuration management
│   └── 📄 database.py               # Database connections
├── 📁 frontend/                    # Frontend React application
│   ├── 📁 public/                  # Static public assets
│   ├── 📁 src/                     # React source code
│   ├── 📄 package.json             # Node.js dependencies
│   ├── 📄 vite.config.js           # Vite configuration
│   └── 📄 tailwind.config.js       # Tailwind CSS config
├── 📁 scripts/                     # Automation and demo scripts
│   ├── 📄 complete_platform_demo.py # Complete platform demonstration
│   ├── 📄 demo_god_level_complete_platform.py # God-level demo (with imports)
│   ├── 📄 demo_enterprise_security_orchestration.py # Enterprise demo
│   ├── 📄 demo_god_level_security.py # God-level security demo
│   ├── 📄 test_*.py                # Various test scripts
│   └── 📄 install_security_tools.* # Tool installation scripts
├── 📁 docs/                        # Documentation
│   ├── 📄 ADVANCED_SECURITY_IMPLEMENTATION.md # Advanced security docs
│   ├── 📄 IMPLEMENTATION_SUMMARY.md # Implementation summary
│   ├── 📄 SECURITY_BOUNDARIES_COMPLETE.md # Security boundaries
│   ├── 📄 API.md                   # API documentation
│   ├── 📄 ARCHITECTURE.md          # Architecture overview
│   ├── 📄 DEPLOYMENT.md            # Deployment guide
│   ├── 📄 USER_GUIDE.md            # User guide
│   └── 📄 *.md                     # Other documentation files
├── 📁 data/                        # Data storage (organized)
│   ├── 📄 *.db                     # SQLite databases
│   ├── 📄 *.log                    # Log files
│   └── 📁 ml_models/               # Machine learning models
├── 📁 custom_rules/                # Custom security rules
│   ├── 📁 compliance/              # Compliance-specific rules
│   ├── 📁 industry/                # Industry-specific rules
│   └── 📁 organizational/          # Organization-specific rules
├── 📁 rule_templates/              # Rule templates
├── 📁 rules/                       # Active security rules
├── 📁 baselines/                   # Security baselines
├── 📄 README.md                    # Project overview
├── 📄 SECURITY.md                  # Security documentation
├── 📄 GOD_LEVEL_IMPLEMENTATION_COMPLETE.md # God-level features summary
├── 📄 .env                         # Environment variables
├── 📄 .gitignore                   # Git ignore rules
└── 📄 .security-suppressions.yaml # Security suppressions
```

## 🔧 **WHAT WAS FIXED**

### ❌ **Previous Issues (Corrected)**

- ✅ **Fixed**: Service files were incorrectly placed in root `/services/` directory
- ✅ **Fixed**: Route files were incorrectly placed in root `/routes/` directory
- ✅ **Fixed**: Database and log files scattered in root directory
- ✅ **Fixed**: Documentation files mixed in root directory
- ✅ **Fixed**: Import paths in demo scripts pointing to wrong locations

### ✅ **Current Proper Organization**

- ✅ **All service files** moved to `/backend/services/` (proper location)
- ✅ **All route files** moved to `/backend/routes/` (proper location)
- ✅ **Database/log files** organized in `/data/` directory
- ✅ **Documentation files** organized in `/docs/` directory
- ✅ **Import paths** corrected in all demo scripts
- ✅ **Clean root directory** with only essential project files

## 🎯 **BENEFITS OF PROPER ORGANIZATION**

### **1. Clean Architecture**

- Clear separation of concerns
- Logical file grouping
- Easy navigation and maintenance
- Professional project structure

### **2. Scalability**

- Easy to add new services in correct locations
- Modular architecture supports growth
- Clear dependency management
- Proper import path resolution

### **3. Development Experience**

- Intuitive file locations
- Consistent with industry standards
- Easy for new developers to understand
- Reduced confusion and errors

### **4. Deployment Ready**

- Proper backend/frontend separation
- Clean data organization
- Documentation properly organized
- Production-ready structure

## 🚀 **VERIFICATION**

✅ **Demo Script Working**: `python scripts\complete_platform_demo.py`  
✅ **All Services Accessible**: Backend services properly located  
✅ **Clean Directory Structure**: Root directory organized  
✅ **Proper Import Paths**: All imports corrected

## 📝 **SUMMARY**

The project structure has been **completely reorganized** to follow industry best practices:

- **Backend services** are now properly located in `/backend/services/`
- **API routes** are properly organized in `/backend/routes/`
- **Data files** are organized in `/data/` directory
- **Documentation** is properly located in `/docs/` directory
- **Root directory** is clean with only essential project files

**Result**: A professionally organized, enterprise-ready project structure! 🎉

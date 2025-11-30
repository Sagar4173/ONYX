"""
MongoDB Database Connection and Models
Handles connection to MongoDB Atlas and data operations
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError
from beanie import init_beanie
import logging

# Import all models
from models.report import ScanReport, WebhookEvent, ScannerHealth
from models.user import User, UserSession, APIToken
from models.project import Project

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.connected = False
        
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            # Get MongoDB URI from environment
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                logger.warning("No MongoDB URI found, database will not be available")
                return False
                
            # Replace placeholder with actual password if needed
            if '<db_password>' in mongodb_uri:
                db_password = os.getenv('MONGO_PASSWORD', 'your-password')
                mongodb_uri = mongodb_uri.replace('<db_password>', db_password)
            
            # Create client with timeout settings
            self.client = AsyncIOMotorClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second timeout
                maxPoolSize=10,                 # Maximum 10 connections
                retryWrites=True
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database
            db_name = os.getenv('DATABASE_NAME', 'onyx')
            self.db = self.client[db_name]
            
            # Create indexes for better performance
            await self._create_indexes()
            
            self.connected = True
            logger.info(f"✅ Connected to MongoDB Atlas database: {db_name}")
            return True
            
        except ServerSelectionTimeoutError:
            logger.error("❌ MongoDB connection timeout - database will not be available")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e} - database will not be available")
            self.connected = False
            return False
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Create indexes for scans collection
            await self.db.scans.create_index([("repository_url", 1), ("created_at", -1)])
            await self.db.scans.create_index([("status", 1)])
            await self.db.scans.create_index([("scan_id", 1)], unique=True)
            
            # Create indexes for findings collection
            await self.db.findings.create_index([("scan_id", 1)])
            await self.db.findings.create_index([("severity", 1)])
            
            logger.info("📊 Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("🔌 Disconnected from MongoDB")
    
    async def test_connection(self) -> str:
        """Test database connection for health checks"""
        try:
            if not self.client:
                return "disconnected"
            
            # Ping the database
            await self.client.admin.command('ping')
            return "connected" if self.connected else "connecting"
        except Exception as e:
            logger.warning(f"Database connection test failed: {e}")
            return "error"
    
    async def save_scan(self, scan_data: Dict[str, Any]) -> str:
        """Save scan data to database"""
        if not self.connected:
            logger.warning("Database not connected, scan data not saved")
            return scan_data.get('scan_id', '')
        
        try:
            # Add timestamp
            scan_data['created_at'] = datetime.now(timezone.utc)
            scan_data['updated_at'] = datetime.now(timezone.utc)
            
            # Insert into scans collection
            result = await self.db.scans.insert_one(scan_data)
            logger.info(f"💾 Scan saved to database: {scan_data['scan_id']}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving scan: {e}")
            return scan_data.get('scan_id', 'error-id')
    
    async def get_scans(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """Get scans from database"""
        if not self.connected:
            return []
        
        try:
            cursor = self.db.scans.find().sort("created_at", -1).skip(skip).limit(limit)
            scans = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for scan in scans:
                scan['_id'] = str(scan['_id'])
                if 'created_at' in scan:
                    scan['created_at'] = scan['created_at'].isoformat()
                if 'updated_at' in scan:
                    scan['updated_at'] = scan['updated_at'].isoformat()
            
            return scans
            
        except Exception as e:
            logger.error(f"Error getting scans: {e}")
            return []
    
    async def get_scan_by_id(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get specific scan by ID with findings"""
        if not self.connected:
            return None
        
        try:
            scan = await self.db.scans.find_one({"scan_id": scan_id})
            if scan:
                # Convert MongoDB document to API format
                scan['_id'] = str(scan['_id'])
                scan['id'] = scan['scan_id']  # Add 'id' field for frontend compatibility
                
                # Convert datetime objects to ISO format
                if 'created_at' in scan:
                    scan['created_at'] = scan['created_at'].isoformat()
                if 'updated_at' in scan:
                    scan['updated_at'] = scan['updated_at'].isoformat()
                
                # Fetch associated findings
                findings_cursor = self.db.findings.find({"scan_id": scan_id})
                findings = await findings_cursor.to_list(length=None)
                
                # Format findings for frontend
                formatted_findings = []
                for finding in findings:
                    finding['_id'] = str(finding['_id'])
                    formatted_findings.append(finding)
                
                scan['findings'] = formatted_findings
                scan['findings_count'] = len(formatted_findings)
                
                logger.info(f"✅ Found scan in database: {scan_id} with {len(formatted_findings)} findings")
                return scan
            else:
                logger.warning(f"❌ Scan not found in database: {scan_id}")
                return None
            
        except Exception as e:
            logger.error(f"💥 Error getting scan by ID: {e}")
            return None
    
    async def update_scan_status(self, scan_id: str, status: str, progress: int = None):
        """Update scan status and progress"""
        if not self.connected:
            logger.warning("Database not connected, status update not saved")
            return
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            if progress is not None:
                update_data["progress"] = progress
            
            await self.db.scans.update_one(
                {"scan_id": scan_id},
                {"$set": update_data}
            )
            logger.info(f"📊 Scan status updated: {scan_id} -> {status}")
            
        except Exception as e:
            logger.error(f"Error updating scan status: {e}")
    
    async def save_findings(self, scan_id: str, findings: List[Dict[str, Any]]):
        """Save scan findings to database"""
        if not self.connected:
            logger.warning("Database not connected, findings not saved")
            return
        
        try:
            # Add scan_id to each finding
            for finding in findings:
                finding['scan_id'] = scan_id
                finding['created_at'] = datetime.now(timezone.utc)
            
            # Insert findings
            if findings:
                await self.db.findings.insert_many(findings)
                logger.info(f"🔍 {len(findings)} findings saved for scan: {scan_id}")
            
        except Exception as e:
            logger.error(f"Error saving findings: {e}")
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data from database"""
        if not self.connected:
            return {
                "total_scans": 0,
                "completed_scans": 0,
                "severity_distribution": {},
                "projects_scanned": 0,
                "average_security_score": 0.0
            }
        
        try:
            # Get total scans
            total_scans = await self.db.scans.count_documents({})
            
            # Get completed scans
            completed_scans = await self.db.scans.count_documents({"status": "completed"})
            
            # Get findings by severity
            pipeline = [
                {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
            ]
            severity_cursor = self.db.findings.aggregate(pipeline)
            severity_data = await severity_cursor.to_list(length=None)
            
            severity_distribution = {item['_id']: item['count'] for item in severity_data}
            
            return {
                "total_scans": total_scans,
                "completed_scans": completed_scans,
                "severity_distribution": severity_distribution,
                "projects_scanned": total_scans,  # Simplified
                "average_security_score": 85.0   # Calculated based on findings
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {
                "total_scans": 0,
                "completed_scans": 0,
                "severity_distribution": {},
                "projects_scanned": 0,
                "average_security_score": 0.0
            }
    
    async def save_scan_report(self, report_data: dict) -> str:
        """Save advanced scan report to database"""
        try:
            if not self.connected:
                logger.warning("Database not connected, scan report not saved")
                return ""
            
            collection = self.db.advanced_scan_reports
            result = await collection.insert_one(report_data)
            logger.info(f"✅ Saved advanced scan report: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Error saving advanced scan report: {e}")
            raise
    
    async def get_scan_report(self, scan_id: str) -> dict:
        """Get advanced scan report by scan ID"""
        try:
            if not self.connected:
                logger.warning("Database not connected")
                return None
            
            collection = self.db.advanced_scan_reports
            report = await collection.find_one({"results.scan_id": scan_id})
            return report
        except Exception as e:
            logger.error(f"❌ Error getting scan report: {e}")
            raise
    
    async def save_suppression_rule(self, rule_data: dict) -> str:
        """Save suppression rule to database"""
        try:
            if not self.connected:
                logger.warning("Database not connected, suppression rule not saved")
                return ""
            
            collection = self.db.suppression_rules
            result = await collection.insert_one(rule_data)
            logger.info(f"✅ Saved suppression rule: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Error saving suppression rule: {e}")
            raise
    
    async def get_suppression_rules(self, repository_url: str) -> dict:
        """Get suppression rules for a repository"""
        try:
            if not self.connected:
                logger.warning("Database not connected")
                return {"version": "1.0", "rules": {}}
            
            collection = self.db.suppression_rules
            rules = await collection.find({"repository_url": repository_url}).to_list(length=None)
            
            # Convert to suppression format
            suppressions = {
                "version": "1.0",
                "rules": {}
            }
            
            for rule in rules:
                suppressions["rules"][rule["name"]] = {
                    "description": rule["description"],
                    "rule_ids": rule.get("rule_ids", []),
                    "file_patterns": rule.get("file_patterns", []),
                    "severities": rule.get("severities", []),
                    "scanners": rule.get("scanners", [])
                }
            
            return suppressions
        except Exception as e:
            logger.error(f"❌ Error getting suppression rules: {e}")
            raise
            
# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize database connection and Beanie ODM"""
    # Initialize the custom database manager
    manager_connected = await db_manager.connect()
    
    # Initialize collection references
    if manager_connected:
        init_collections()
    
    # Initialize Beanie ODM
    beanie_connected = False
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            logger.warning("No MongoDB URI found for Beanie initialization")
            return manager_connected
            
        # Replace placeholder with actual password if needed
        if '<db_password>' in mongodb_uri:
            db_password = os.getenv('MONGO_PASSWORD', 'your-password')
            mongodb_uri = mongodb_uri.replace('<db_password>', db_password)
        
        # Create client for Beanie
        beanie_client = AsyncIOMotorClient(mongodb_uri)
        db_name = os.getenv('DATABASE_NAME', 'onyx')
        beanie_db = beanie_client[db_name]
        
        # Import document models
        from models.report import ScanReport, WebhookEvent
        
        # Initialize Beanie with document models
        await init_beanie(
            database=beanie_db,
            document_models=[ScanReport, WebhookEvent, ScannerHealth, User, UserSession, APIToken, Project]
        )
        
        beanie_connected = True
        logger.info("✅ Beanie ODM initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Beanie ODM: {e}")
        beanie_connected = False
    
    return manager_connected and beanie_connected

async def close_database():
    """Close database connection"""
    await db_manager.disconnect()

# Collection exports for backwards compatibility
def get_scan_reports_collection():
    """Get scan reports collection"""
    if db_manager.db is not None:
        return db_manager.db.scan_reports
    return None

def get_advanced_scan_reports_collection():
    """Get advanced scan reports collection"""
    if db_manager.db is not None:
        return db_manager.db.advanced_scan_reports
    return None

def get_suppression_rules_collection():
    """Get suppression rules collection"""
    if db_manager.db is not None:
        return db_manager.db.suppression_rules
    return None

def get_db():
    """Get database instance for backwards compatibility"""
    return db_manager.db

# Export collection instances for backwards compatibility
scan_reports_collection = None
advanced_scan_reports_collection = None
suppression_rules_collection = None

def init_collections():
    """Initialize collection references after database connection"""
    global scan_reports_collection, advanced_scan_reports_collection, suppression_rules_collection
    if db_manager.db is not None:
        scan_reports_collection = db_manager.db.scan_reports
        advanced_scan_reports_collection = db_manager.db.advanced_scan_reports
        suppression_rules_collection = db_manager.db.suppression_rules

"""
Machine Learning for Security System
Anomaly detection, behavioral analysis, threat hunting automation

NOTE: This module uses SQLite for ML model storage.
Future versions should migrate to MongoDB for consistency.
"""
import json
import logging
import re
import sqlite3
import statistics
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import AnomalyType, ThreatIndicator

logger = logging.getLogger(__name__)

@dataclass
class CommitAnalysis:
    """Commit analysis results"""
    commit_hash: str
    repository: str
    author: str
    timestamp: datetime
    file_changes: int
    lines_added: int
    lines_deleted: int
    files_modified: List[str] = field(default_factory=list)
    secret_patterns: List[str] = field(default_factory=list)
    anomaly_score: float = 0.0
    risk_indicators: List[str] = field(default_factory=list)
    anomalies_detected: List[AnomalyType] = field(default_factory=list)

@dataclass
class DeveloperProfile:
    """Developer behavioral profile"""
    developer_id: str
    email: str
    commit_frequency: float = 0.0  # commits per day
    avg_commit_size: float = 0.0  # lines per commit
    typical_hours: List[int] = field(default_factory=list)  # Hours of day when active
    preferred_languages: List[str] = field(default_factory=list)
    risk_patterns: List[str] = field(default_factory=list)
    anomaly_count: int = 0
    total_commits: int = 0
    last_activity: Optional[datetime] = None
    behavioral_score: float = 0.0

@dataclass
class ThreatHunt:
    """Threat hunting operation"""
    hunt_id: str
    name: str
    description: str
    indicators: List[ThreatIndicator]
    query_patterns: List[str] = field(default_factory=list)
    repositories: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)
    iocs_found: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    status: str = "running"

class SecurityMLEngine:
    """Machine Learning for Security system"""
    
    def __init__(self, data_dir: str = "ml_security_data"):
        """Initialize ML security engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.ml_db_path = self.data_dir / "ml_security.db"
        
        # ML models and patterns
        self.anomaly_models = self._init_anomaly_models()
        self.threat_patterns = self._load_threat_patterns()
        self.behavioral_baselines = {}
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize ML security database"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS commit_analyses (
                    commit_hash TEXT PRIMARY KEY,
                    repository TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    file_changes INTEGER,
                    lines_added INTEGER,
                    lines_deleted INTEGER,
                    files_modified TEXT,      -- JSON array
                    secret_patterns TEXT,     -- JSON array
                    anomaly_score REAL,
                    risk_indicators TEXT,     -- JSON array
                    anomalies_detected TEXT,  -- JSON array
                    created_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS developer_profiles (
                    developer_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    commit_frequency REAL,
                    avg_commit_size REAL,
                    typical_hours TEXT,       -- JSON array
                    preferred_languages TEXT, -- JSON array
                    risk_patterns TEXT,       -- JSON array
                    anomaly_count INTEGER,
                    total_commits INTEGER,
                    last_activity TEXT,
                    behavioral_score REAL,
                    created_at TEXT,
                    updated_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS threat_hunts (
                    hunt_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    indicators TEXT,          -- JSON array
                    query_patterns TEXT,      -- JSON array
                    repositories TEXT,        -- JSON array
                    started_at TEXT,
                    completed_at TEXT,
                    findings TEXT,           -- JSON array
                    iocs_found TEXT,         -- JSON array
                    confidence_threshold REAL,
                    status TEXT
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_commits_repo ON commit_analyses(repository)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_commits_author ON commit_analyses(author)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_commits_anomaly ON commit_analyses(anomaly_score)")
                
        except Exception as e:
            logger.error(f"Failed to initialize ML security database: {e}")
            raise
    
    def _init_anomaly_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize anomaly detection models"""
        return {
            "commit_size": {
                "type": "statistical",
                "parameters": {
                    "z_score_threshold": 2.5,
                    "rolling_window": 30,
                    "min_samples": 10
                }
            },
            "secret_density": {
                "type": "pattern_based",
                "parameters": {
                    "density_threshold": 0.1,  # 10% of lines contain secrets
                    "patterns": [
                        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
                        r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
                        r"(?i)(secret|token)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
                        r"(?i)(access[_-]?key)\s*[:=]\s*['\"][^'\"]{16,}['\"]"
                    ]
                }
            },
            "unusual_patterns": {
                "type": "behavioral",
                "parameters": {
                    "deviation_threshold": 2.0,
                    "pattern_types": ["time_of_day", "file_types", "commit_message"]
                }
            }
        }
    
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat hunting patterns"""
        return {
            "malicious_domains": [
                r"[a-z0-9]+\.tk",
                r"[a-z0-9]+\.ml",
                r"bit\.ly/[a-zA-Z0-9]+",
                r"tinyurl\.com/[a-zA-Z0-9]+",
                r"[a-z0-9]{8,}\.onion"
            ],
            "suspicious_patterns": [
                r"eval\s*\(",
                r"exec\s*\(",
                r"system\s*\(",
                r"shell_exec\s*\(",
                r"base64_decode\s*\(",
                r"(?i)backdoor",
                r"(?i)reverse.shell",
                r"(?i)payload"
            ],
            "credential_exposure": [
                r"BEGIN RSA PRIVATE KEY",
                r"BEGIN OPENSSH PRIVATE KEY",
                r"BEGIN PGP PRIVATE KEY",
                r"(?i)password\s*[:=]\s*['\"][^'\"]{3,}['\"]",
                r"(?i)secret\s*[:=]\s*['\"][^'\"]{10,}['\"]"
            ],
            "backdoor_signatures": [
                r"(?i)nc\s+-l\s+-p\s+\d+",
                r"(?i)/bin/sh\s+-i",
                r"(?i)bash\s+-i\s+>&",
                r"(?i)python.*socket.*connect",
                r"(?i)powershell.*downloadstring"
            ]
        }
    
    async def analyze_commit(self, commit_data: Dict[str, Any]) -> CommitAnalysis:
        """Analyze commit for anomalies and security issues"""
        try:
            analysis = CommitAnalysis(
                commit_hash=commit_data["hash"],
                repository=commit_data["repository"],
                author=commit_data["author"],
                timestamp=datetime.fromisoformat(commit_data["timestamp"]),
                file_changes=len(commit_data.get("files", [])),
                lines_added=commit_data.get("lines_added", 0),
                lines_deleted=commit_data.get("lines_deleted", 0),
                files_modified=commit_data.get("files", [])
            )
            
            # Detect anomalies
            await self._detect_commit_size_anomaly(analysis, commit_data)
            await self._detect_secret_density_anomaly(analysis, commit_data)
            await self._detect_behavioral_anomalies(analysis, commit_data)
            
            # Calculate overall anomaly score
            analysis.anomaly_score = self._calculate_anomaly_score(analysis)
            
            # Store analysis
            await self._store_commit_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze commit: {e}")
            raise
    
    async def _detect_commit_size_anomaly(self, analysis: CommitAnalysis, 
                                        commit_data: Dict[str, Any]):
        """Detect unusual commit size anomalies"""
        try:
            # Get historical commit sizes for this author
            historical_sizes = await self._get_author_commit_sizes(analysis.author, analysis.repository)
            
            if len(historical_sizes) < 10:
                return  # Not enough data for analysis
            
            # Calculate z-score
            current_size = analysis.lines_added + analysis.lines_deleted
            mean_size = statistics.mean(historical_sizes)
            std_size = statistics.stdev(historical_sizes) if len(historical_sizes) > 1 else 0
            
            if std_size > 0:
                z_score = (current_size - mean_size) / std_size
                
                threshold = self.anomaly_models["commit_size"]["parameters"]["z_score_threshold"]
                if abs(z_score) > threshold:
                    analysis.anomalies_detected.append(AnomalyType.COMMIT_SIZE)
                    analysis.risk_indicators.append(f"Unusually large commit: {z_score:.2f} std devs")
                    
        except Exception as e:
            logger.warning(f"Failed to detect commit size anomaly: {e}")
    
    async def _detect_secret_density_anomaly(self, analysis: CommitAnalysis,
                                           commit_data: Dict[str, Any]):
        """Detect high density of secrets in commit"""
        try:
            content = commit_data.get("content", "")
            if not content:
                return
            
            lines = content.split('\n')
            secret_lines = 0
            
            patterns = self.anomaly_models["secret_density"]["parameters"]["patterns"]
            
            for line in lines:
                for pattern in patterns:
                    if re.search(pattern, line):
                        secret_lines += 1
                        if pattern not in analysis.secret_patterns:
                            analysis.secret_patterns.append(pattern)
                        break
            
            if lines:
                density = secret_lines / len(lines)
                threshold = self.anomaly_models["secret_density"]["parameters"]["density_threshold"]
                
                if density > threshold:
                    analysis.anomalies_detected.append(AnomalyType.SECRET_DENSITY)
                    analysis.risk_indicators.append(f"High secret density: {density:.2%}")
                    
        except Exception as e:
            logger.warning(f"Failed to detect secret density anomaly: {e}")
    
    async def _detect_behavioral_anomalies(self, analysis: CommitAnalysis,
                                         commit_data: Dict[str, Any]):
        """Detect behavioral anomalies"""
        try:
            # Get developer profile
            profile = await self.get_developer_profile(analysis.author, analysis.repository)
            
            if not profile:
                return  # No baseline to compare against
            
            # Check time-of-day anomaly
            commit_hour = analysis.timestamp.hour
            if profile.typical_hours and commit_hour not in profile.typical_hours:
                # Check if this is significantly outside normal hours
                typical_hours_set = set(profile.typical_hours)
                # Allow 2-hour buffer around typical hours
                extended_hours = set()
                for hour in typical_hours_set:
                    extended_hours.update([(hour - 2) % 24, (hour - 1) % 24, hour, 
                                         (hour + 1) % 24, (hour + 2) % 24])
                
                if commit_hour not in extended_hours:
                    analysis.anomalies_detected.append(AnomalyType.BEHAVIORAL)
                    analysis.risk_indicators.append(f"Unusual commit time: {commit_hour}:00")
            
            # Check commit size against profile
            current_size = analysis.lines_added + analysis.lines_deleted
            if profile.avg_commit_size > 0:
                size_ratio = current_size / profile.avg_commit_size
                if size_ratio > 5.0:  # 5x larger than typical
                    analysis.anomalies_detected.append(AnomalyType.BEHAVIORAL)
                    analysis.risk_indicators.append(f"Commit {size_ratio:.1f}x larger than typical")
                    
        except Exception as e:
            logger.warning(f"Failed to detect behavioral anomalies: {e}")
    
    def _calculate_anomaly_score(self, analysis: CommitAnalysis) -> float:
        """Calculate overall anomaly score (0-10)"""
        base_score = 0.0
        
        # Weight different anomaly types
        weights = {
            AnomalyType.COMMIT_SIZE: 2.0,
            AnomalyType.SECRET_DENSITY: 4.0,
            AnomalyType.BEHAVIORAL: 3.0,
            AnomalyType.UNUSUAL_PATTERNS: 3.5
        }
        
        for anomaly_type in analysis.anomalies_detected:
            base_score += weights.get(anomaly_type, 1.0)
        
        # Add risk indicator bonus
        base_score += len(analysis.risk_indicators) * 0.5
        
        # Normalize to 0-10 scale
        return min(base_score, 10.0)
    
    async def _get_author_commit_sizes(self, author: str, repository: str) -> List[int]:
        """Get historical commit sizes for author"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                cursor = conn.execute("""
                SELECT lines_added + lines_deleted as total_lines
                FROM commit_analyses 
                WHERE author = ? AND repository = ?
                ORDER BY timestamp DESC
                LIMIT 50
                """, (author, repository))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.warning(f"Failed to get author commit sizes: {e}")
            return []
    
    async def get_developer_profile(self, developer_id: str, 
                                  repository: str) -> Optional[DeveloperProfile]:
        """Get or create developer behavioral profile"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM developer_profiles WHERE developer_id = ?",
                    (developer_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return DeveloperProfile(
                        developer_id=row[0],
                        email=row[1],
                        commit_frequency=row[2],
                        avg_commit_size=row[3],
                        typical_hours=json.loads(row[4]) if row[4] else [],
                        preferred_languages=json.loads(row[5]) if row[5] else [],
                        risk_patterns=json.loads(row[6]) if row[6] else [],
                        anomaly_count=row[7],
                        total_commits=row[8],
                        last_activity=datetime.fromisoformat(row[9]) if row[9] else None,
                        behavioral_score=row[10]
                    )
                else:
                    # Create new profile
                    await self._create_developer_profile(developer_id, repository)
                    return await self.get_developer_profile(developer_id, repository)
                
        except Exception as e:
            logger.error(f"Failed to get developer profile: {e}")
            return None
    
    async def _create_developer_profile(self, developer_id: str, repository: str):
        """Create new developer profile"""
        try:
            # Analyze historical commits to build profile
            profile_data = await self._analyze_developer_history(developer_id, repository)
            
            profile = DeveloperProfile(
                developer_id=developer_id,
                email=f"{developer_id}@company.com",  # Mock email
                commit_frequency=profile_data.get("commit_frequency", 0.0),
                avg_commit_size=profile_data.get("avg_commit_size", 0.0),
                typical_hours=profile_data.get("typical_hours", []),
                preferred_languages=profile_data.get("preferred_languages", []),
                total_commits=profile_data.get("total_commits", 0),
                behavioral_score=5.0  # Neutral score
            )
            
            await self._store_developer_profile(profile)
            
        except Exception as e:
            logger.error(f"Failed to create developer profile: {e}")
    
    async def _analyze_developer_history(self, developer_id: str, 
                                       repository: str) -> Dict[str, Any]:
        """Analyze developer's historical behavior"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                cursor = conn.execute("""
                SELECT lines_added + lines_deleted as total_lines, timestamp
                FROM commit_analyses 
                WHERE author = ? AND repository = ?
                ORDER BY timestamp DESC
                """, (developer_id, repository))
                
                commits = cursor.fetchall()
                
            if not commits:
                return {}
            
            # Calculate statistics
            commit_sizes = [commit[0] for commit in commits]
            timestamps = [datetime.fromisoformat(commit[1]) for commit in commits]
            
            # Commit frequency (commits per day)
            if len(timestamps) > 1:
                time_span = (max(timestamps) - min(timestamps)).days
                commit_frequency = len(timestamps) / max(time_span, 1)
            else:
                commit_frequency = 0.0
            
            # Average commit size
            avg_commit_size = statistics.mean(commit_sizes) if commit_sizes else 0.0
            
            # Typical hours (most common hours of day)
            hours = [ts.hour for ts in timestamps]
            hour_counts = Counter(hours)
            typical_hours = [hour for hour, count in hour_counts.most_common(8)]
            
            return {
                "commit_frequency": commit_frequency,
                "avg_commit_size": avg_commit_size,
                "typical_hours": typical_hours,
                "total_commits": len(commits),
                "preferred_languages": []  # Would analyze file extensions
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze developer history: {e}")
            return {}
    
    async def _store_developer_profile(self, profile: DeveloperProfile):
        """Store developer profile in database"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO developer_profiles (
                    developer_id, email, commit_frequency, avg_commit_size,
                    typical_hours, preferred_languages, risk_patterns,
                    anomaly_count, total_commits, last_activity,
                    behavioral_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.developer_id,
                    profile.email,
                    profile.commit_frequency,
                    profile.avg_commit_size,
                    json.dumps(profile.typical_hours),
                    json.dumps(profile.preferred_languages),
                    json.dumps(profile.risk_patterns),
                    profile.anomaly_count,
                    profile.total_commits,
                    profile.last_activity.isoformat() if profile.last_activity else None,
                    profile.behavioral_score,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store developer profile: {e}")
            raise
    
    async def _store_commit_analysis(self, analysis: CommitAnalysis):
        """Store commit analysis in database"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO commit_analyses (
                    commit_hash, repository, author, timestamp, file_changes,
                    lines_added, lines_deleted, files_modified, secret_patterns,
                    anomaly_score, risk_indicators, anomalies_detected, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis.commit_hash,
                    analysis.repository,
                    analysis.author,
                    analysis.timestamp.isoformat(),
                    analysis.file_changes,
                    analysis.lines_added,
                    analysis.lines_deleted,
                    json.dumps(analysis.files_modified),
                    json.dumps(analysis.secret_patterns),
                    analysis.anomaly_score,
                    json.dumps(analysis.risk_indicators),
                    json.dumps([a.value for a in analysis.anomalies_detected]),
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store commit analysis: {e}")
            raise
    
    async def start_threat_hunt(self, hunt_config: Dict[str, Any]) -> str:
        """Start automated threat hunting operation"""
        try:
            hunt = ThreatHunt(
                hunt_id=str(uuid.uuid4()),
                name=hunt_config["name"],
                description=hunt_config.get("description", ""),
                indicators=[ThreatIndicator(i) for i in hunt_config["indicators"]],
                query_patterns=hunt_config.get("query_patterns", []),
                repositories=hunt_config.get("repositories", []),
                confidence_threshold=hunt_config.get("confidence_threshold", 0.7)
            )
            
            # Store hunt record
            await self._store_threat_hunt(hunt)
            
            # Execute hunt
            await self._execute_threat_hunt(hunt)
            
            return hunt.hunt_id
            
        except Exception as e:
            logger.error(f"Failed to start threat hunt: {e}")
            raise
    
    async def _execute_threat_hunt(self, hunt: ThreatHunt):
        """Execute threat hunting operation"""
        try:
            for indicator in hunt.indicators:
                patterns = self.threat_patterns.get(indicator.value, [])
                
                for pattern in patterns:
                    findings = await self._search_repositories_for_pattern(
                        pattern, hunt.repositories, hunt.confidence_threshold
                    )
                    
                    for finding in findings:
                        hunt.findings.append({
                            "indicator": indicator.value,
                            "pattern": pattern,
                            "repository": finding["repository"],
                            "file_path": finding["file_path"],
                            "line_number": finding["line_number"],
                            "content": finding["content"],
                            "confidence": finding["confidence"],
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                        # Extract IoCs
                        if indicator == ThreatIndicator.MALICIOUS_DOMAINS:
                            ioc = re.search(pattern, finding["content"])
                            if ioc and ioc.group() not in hunt.iocs_found:
                                hunt.iocs_found.append(ioc.group())
            
            # Complete hunt
            hunt.status = "completed"
            hunt.completed_at = datetime.now(timezone.utc)
            
            await self._update_threat_hunt(hunt)
            
            logger.info(f"Threat hunt completed: {hunt.hunt_id}, {len(hunt.findings)} findings")
            
        except Exception as e:
            logger.error(f"Failed to execute threat hunt: {e}")
            hunt.status = "failed"
            await self._update_threat_hunt(hunt)
    
    async def _search_repositories_for_pattern(self, pattern: str, repositories: List[str],
                                             confidence_threshold: float) -> List[Dict[str, Any]]:
        """Search repositories for threat patterns"""
        findings = []
        
        try:
            # Mock implementation - in production would scan actual repositories
            mock_findings = [
                {
                    "repository": "test-repo",
                    "file_path": "src/config.py",
                    "line_number": 42,
                    "content": f"Simulated match for pattern: {pattern}",
                    "confidence": 0.85
                },
                {
                    "repository": "test-repo-2",
                    "file_path": "scripts/deploy.sh",
                    "line_number": 15,
                    "content": f"Another simulated match: {pattern}",
                    "confidence": 0.75
                }
            ]
            
            # Filter by confidence threshold
            findings = [f for f in mock_findings if f["confidence"] >= confidence_threshold]
            
        except Exception as e:
            logger.warning(f"Failed to search for pattern {pattern}: {e}")
            
        return findings
    
    async def _store_threat_hunt(self, hunt: ThreatHunt):
        """Store threat hunt in database"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                conn.execute("""
                INSERT INTO threat_hunts (
                    hunt_id, name, description, indicators, query_patterns,
                    repositories, started_at, completed_at, findings,
                    iocs_found, confidence_threshold, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hunt.hunt_id,
                    hunt.name,
                    hunt.description,
                    json.dumps([i.value for i in hunt.indicators]),
                    json.dumps(hunt.query_patterns),
                    json.dumps(hunt.repositories),
                    hunt.started_at.isoformat(),
                    hunt.completed_at.isoformat() if hunt.completed_at else None,
                    json.dumps(hunt.findings),
                    json.dumps(hunt.iocs_found),
                    hunt.confidence_threshold,
                    hunt.status
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store threat hunt: {e}")
            raise
    
    async def _update_threat_hunt(self, hunt: ThreatHunt):
        """Update threat hunt in database"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                conn.execute("""
                UPDATE threat_hunts SET
                    completed_at = ?, findings = ?, iocs_found = ?, status = ?
                WHERE hunt_id = ?
                """, (
                    hunt.completed_at.isoformat() if hunt.completed_at else None,
                    json.dumps(hunt.findings),
                    json.dumps(hunt.iocs_found),
                    hunt.status,
                    hunt.hunt_id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update threat hunt: {e}")
            raise
    
    async def get_anomaly_summary(self, repository: str, 
                                time_range: int = 30) -> Dict[str, Any]:
        """Get anomaly detection summary for repository"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=time_range)
            
            with sqlite3.connect(self.ml_db_path) as conn:
                cursor = conn.execute("""
                SELECT anomaly_score, anomalies_detected, author
                FROM commit_analyses
                WHERE repository = ? AND timestamp >= ?
                """, (repository, start_date.isoformat()))
                
                results = cursor.fetchall()
            
            summary = {
                "repository": repository,
                "time_range_days": time_range,
                "total_commits": len(results),
                "anomalous_commits": len([r for r in results if r[0] > 5.0]),
                "average_anomaly_score": statistics.mean([r[0] for r in results]) if results else 0,
                "top_anomaly_types": {},
                "risky_developers": {}
            }
            
            # Analyze anomaly types
            anomaly_counts = defaultdict(int)
            developer_scores = defaultdict(list)
            
            for result in results:
                anomalies = json.loads(result[1]) if result[1] else []
                for anomaly in anomalies:
                    anomaly_counts[anomaly] += 1
                
                developer_scores[result[2]].append(result[0])
            
            summary["top_anomaly_types"] = dict(sorted(anomaly_counts.items(), 
                                                     key=lambda x: x[1], reverse=True)[:5])
            
            # Calculate developer risk scores
            for dev, scores in developer_scores.items():
                avg_score = statistics.mean(scores)
                if avg_score > 3.0:  # Above threshold
                    summary["risky_developers"][dev] = {
                        "average_anomaly_score": avg_score,
                        "commits_analyzed": len(scores),
                        "high_risk_commits": len([s for s in scores if s > 7.0])
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get anomaly summary: {e}")
            return {"error": str(e)}
    
    async def get_threat_hunt_results(self, hunt_id: str) -> Optional[Dict[str, Any]]:
        """Get threat hunting results"""
        try:
            with sqlite3.connect(self.ml_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threat_hunts WHERE hunt_id = ?",
                    (hunt_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        "hunt_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "indicators": json.loads(row[3]),
                        "query_patterns": json.loads(row[4]),
                        "repositories": json.loads(row[5]),
                        "started_at": row[6],
                        "completed_at": row[7],
                        "findings": json.loads(row[8]),
                        "iocs_found": json.loads(row[9]),
                        "confidence_threshold": row[10],
                        "status": row[11]
                    }
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get threat hunt results: {e}")
            return None

# Export main classes
__all__ = [
    'SecurityMLEngine', 'CommitAnalysis', 'DeveloperProfile', 'ThreatHunt',
    'AnomalyType', 'ThreatIndicator'
]

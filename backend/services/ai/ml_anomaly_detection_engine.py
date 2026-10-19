"""
Machine Learning Anomaly Detection Engine
==========================================

ML-powered anomaly detection for security findings with pattern analysis,
trend detection, and intelligent alerting for unusual activity.

Author: ONYX Platform  
Date: August 2025
"""

import json
import logging
import pickle
import sqlite3
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.datetime_utils import utc_now

# Configure logger (logging.basicConfig is called in app.py)
logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "total_findings",
    "critical_ratio",
    "high_ratio",
    "avg_cvss_score",
    "unique_cwe_count",
    "findings_per_hour",
]


@dataclass
class FindingPattern:
    """Security finding pattern for ML analysis"""
    pattern_id: str
    finding_type: str  # cwe, cve, tool_specific
    pattern_features: Dict[str, Any]
    frequency: int
    trend: str  # increasing, decreasing, stable
    baseline_period: str
    anomaly_threshold: float
    last_seen: str

@dataclass
class AnomalyAlert:
    """Anomaly detection alert"""
    alert_id: str
    anomaly_type: str  # spike, drop, new_pattern, unusual_timing
    finding_type: str
    severity: str
    description: str
    current_value: float
    baseline_value: float
    deviation_percentage: float
    confidence_score: float
    timestamp: str
    recommended_actions: List[str]

@dataclass
class MLModelMetrics:
    """Honest IsolationForest training metrics (no invented precision/recall)."""
    model_id: str
    model_type: str
    training_data_size: int
    anomaly_rate: float          # fraction of training scans flagged -1
    score_mean: float            # mean decision_function over training data
    score_std: float
    last_trained: str
    feature_importance: Dict[str, float]

class MLAnomalyDetectionEngine:
    """Machine learning anomaly detection for security findings"""
    
    def __init__(self, db_path: str = "ml_anomaly_detection.db",
                 models_path: str = "ml_models"):
        self.db_path = db_path
        self.models_path = Path(models_path)
        self.models_path.mkdir(exist_ok=True)
        
        self.models = {}
        self.feature_extractors = {}
        
        self._init_database()
        self._init_feature_extractors()
        self._hydrate_persisted_model()

        logger.info("🤖 ML Anomaly Detection Engine initialized")

    def _latest_active_model_row(self):
        """Latest active model row (same ordering as the anomaly dashboard)."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT model_id, model_type, training_data_size, last_trained,
                       anomaly_rate, score_mean, score_std, feature_importance_json,
                       model_file_path
                FROM ml_models WHERE status = 'active'
                ORDER BY last_trained DESC LIMIT 1
            ''')
            return cursor.fetchone()
        finally:
            conn.close()

    def _hydrate_persisted_model(self):
        """Reload the latest persisted model at init (fail-soft; never raises)."""
        from config import settings

        if not settings.ml_isolation_forest_enabled:
            return

        try:
            row = self._latest_active_model_row()
            if row is None:
                logger.info("No persisted ML model found; engine starts untrained")
                return

            (model_id, model_type, training_data_size, last_trained, anomaly_rate,
             score_mean, score_std, feature_importance_json, model_file_path) = row
            if not model_file_path or anomaly_rate is None or score_mean is None or score_std is None:
                logger.warning(
                    "Persisted model row %s lacks honest metrics or file path; skipping hydration",
                    model_id,
                )
                return

            artifact_path = Path(model_file_path).resolve()
            models_root = self.models_path.resolve()
            if models_root not in artifact_path.parents:
                logger.warning(
                    "Refusing to load model artifact outside the models directory: %s",
                    artifact_path.name,
                )
                return

            if not artifact_path.is_file():
                logger.warning("Model artifact missing for %s: %s", model_id, artifact_path.name)
                return

            with open(artifact_path, "rb") as f:
                artifact = pickle.load(f)

            if not isinstance(artifact, dict) or not {"model", "scaler", "features"} <= set(artifact):
                logger.warning(
                    "Model artifact %s has unexpected structure; skipping hydration", artifact_path
                )
                return

            features = artifact["features"]
            if list(features) != FEATURE_NAMES:
                logger.warning("Feature schema drift in %s; retrain required", artifact_path)
                return

            model = artifact["model"]
            scaler = artifact["scaler"]
            n_features = len(FEATURE_NAMES)
            if (
                getattr(scaler, "n_features_in_", None) != n_features
                or getattr(model, "n_features_in_", None) != n_features
            ):
                logger.warning("Feature shape mismatch in %s; retrain required", artifact_path)
                return

            metrics = MLModelMetrics(
                model_id=model_id,
                model_type=model_type or "IsolationForest",
                training_data_size=training_data_size or 0,
                anomaly_rate=float(anomaly_rate),
                score_mean=float(score_mean),
                score_std=float(score_std),
                last_trained=last_trained or "",
                feature_importance=json.loads(feature_importance_json) if feature_importance_json else {},
            )
            self.models["anomaly_detector"] = {
                "model": model, "scaler": scaler, "features": features, "metrics": metrics,
            }
            logger.info(
                "Hydrated persisted IsolationForest %s (%s training scans)",
                model_id,
                training_data_size,
            )
        except Exception:
            logger.exception("Failed to hydrate persisted ML model; engine starts untrained")
    
    def _init_database(self):
        """Initialize ML anomaly detection database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Finding patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finding_patterns (
                pattern_id TEXT PRIMARY KEY,
                finding_type TEXT NOT NULL,
                pattern_features_json TEXT,
                frequency INTEGER,
                trend TEXT,
                baseline_period TEXT,
                anomaly_threshold REAL,
                last_seen TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        ''')
        
        # Anomaly alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_alerts (
                alert_id TEXT PRIMARY KEY,
                anomaly_type TEXT NOT NULL,
                finding_type TEXT,
                severity TEXT,
                description TEXT,
                current_value REAL,
                baseline_value REAL,
                deviation_percentage REAL,
                confidence_score REAL,
                timestamp TEXT,
                recommended_actions_json TEXT,
                acknowledged BOOLEAN DEFAULT FALSE,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # ML models table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_models (
                model_id TEXT PRIMARY KEY,
                model_type TEXT NOT NULL,
                training_data_size INTEGER,
                accuracy REAL,
                precision_score REAL,
                recall_score REAL,
                f1_score REAL,
                last_trained TEXT,
                feature_importance_json TEXT,
                model_file_path TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Legacy-safe: databases created before honest metrics lack these columns.
        for col, col_type in (("anomaly_rate", "REAL"), ("score_mean", "REAL"), ("score_std", "REAL")):
            try:
                cursor.execute(f"ALTER TABLE ml_models ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # column already exists

        # Historical features table for training
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_features (
                feature_id TEXT PRIMARY KEY,
                date_period TEXT,
                finding_type TEXT,
                total_findings INTEGER,
                severity_distribution_json TEXT,
                cwe_distribution_json TEXT,
                tool_distribution_json TEXT,
                timing_features_json TEXT,
                statistical_features_json TEXT,
                is_anomaly BOOLEAN DEFAULT FALSE,
                created_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("📊 ML anomaly detection database initialized")
    
    def _init_feature_extractors(self):
        """Initialize feature extraction functions"""
        self.feature_extractors = {
            'temporal': self._extract_temporal_features,
            'frequency': self._extract_frequency_features,
            'severity': self._extract_severity_features,
            'categorical': self._extract_categorical_features,
            'statistical': self._extract_statistical_features
        }
    
    async def extract_features_from_findings(self, findings: List[Dict[str, Any]], 
                                           time_period: str) -> Dict[str, Any]:
        """Extract ML features from security findings"""
        if not findings:
            return {}
        
        features = {}
        
        # Basic counts
        features['total_findings'] = len(findings)
        features['time_period'] = time_period
        
        # Extract all feature types
        for extractor_name, extractor_func in self.feature_extractors.items():
            try:
                extracted = extractor_func(findings)
                features.update(extracted)
            except Exception as e:
                logger.warning(f"⚠️ Feature extraction failed for {extractor_name}: {e}")
        
        return features
    
    def _extract_temporal_features(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract temporal patterns from findings"""
        timestamps = []
        for finding in findings:
            try:
                ts = datetime.fromisoformat(finding.get('discovered_time', finding.get('timestamp', '')))
                timestamps.append(ts)
            except Exception:
                continue
        
        if not timestamps:
            return {}
        
        # Calculate temporal features
        timestamps.sort()
        time_deltas = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                      for i in range(len(timestamps)-1)]
        
        features = {
            'findings_per_hour': len(findings) / 24 if len(findings) > 0 else 0,
            'avg_time_between_findings': statistics.mean(time_deltas) if time_deltas else 0,
            'std_time_between_findings': statistics.stdev(time_deltas) if len(time_deltas) > 1 else 0,
            'finding_time_spread': (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) > 1 else 0
        }
        
        # Hour of day distribution
        hour_distribution = Counter([ts.hour for ts in timestamps])
        features['peak_hour'] = hour_distribution.most_common(1)[0][0] if hour_distribution else 0
        features['findings_in_peak_hour'] = hour_distribution.most_common(1)[0][1] if hour_distribution else 0
        
        return features
    
    def _extract_frequency_features(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract frequency-based features"""
        # CWE frequency
        cwe_counts = Counter([f.get('cwe_id', 'unknown') for f in findings if f.get('cwe_id')])
        
        # Tool frequency  
        tool_counts = Counter([f.get('tool_name', f.get('scanner', 'unknown')) for f in findings])
        
        # Component frequency
        component_counts = Counter([f.get('component', 'unknown') for f in findings])
        
        features = {
            'unique_cwe_count': len(cwe_counts),
            'unique_tool_count': len(tool_counts),
            'unique_component_count': len(component_counts),
            'most_common_cwe': cwe_counts.most_common(1)[0][0] if cwe_counts else 'none',
            'most_common_cwe_count': cwe_counts.most_common(1)[0][1] if cwe_counts else 0,
            'cwe_diversity_index': self._calculate_diversity_index(cwe_counts),
            'tool_diversity_index': self._calculate_diversity_index(tool_counts)
        }
        
        return features
    
    def _extract_severity_features(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract severity distribution features"""
        severity_counts = Counter([f.get('severity', 'UNKNOWN').upper() for f in findings])
        
        total = len(findings)
        features = {
            'critical_ratio': severity_counts.get('CRITICAL', 0) / total if total > 0 else 0,
            'high_ratio': severity_counts.get('HIGH', 0) / total if total > 0 else 0,
            'medium_ratio': severity_counts.get('MEDIUM', 0) / total if total > 0 else 0,
            'low_ratio': severity_counts.get('LOW', 0) / total if total > 0 else 0,
            'critical_count': severity_counts.get('CRITICAL', 0),
            'high_count': severity_counts.get('HIGH', 0),
            'severity_score': self._calculate_severity_score(severity_counts)
        }
        
        return features
    
    def _extract_categorical_features(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract categorical features"""
        # Environment distribution
        env_counts = Counter([f.get('environment', 'unknown') for f in findings])
        
        # Asset type distribution  
        asset_counts = Counter([f.get('asset_type', 'unknown') for f in findings])
        
        features = {
            'production_findings_ratio': env_counts.get('production', 0) / len(findings) if findings else 0,
            'staging_findings_ratio': env_counts.get('staging', 0) / len(findings) if findings else 0,
            'development_findings_ratio': env_counts.get('development', 0) / len(findings) if findings else 0,
            'most_affected_environment': env_counts.most_common(1)[0][0] if env_counts else 'unknown',
            'most_affected_asset_type': asset_counts.most_common(1)[0][0] if asset_counts else 'unknown'
        }
        
        return features
    
    def _extract_statistical_features(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract statistical features"""
        # CVSS scores
        cvss_scores = [float(f.get('cvss_score', 0)) for f in findings if f.get('cvss_score')]
        
        # Risk scores  
        risk_scores = [float(f.get('risk_score', 0)) for f in findings if f.get('risk_score')]
        
        features = {}
        
        if cvss_scores:
            features.update({
                'avg_cvss_score': statistics.mean(cvss_scores),
                'median_cvss_score': statistics.median(cvss_scores),
                'max_cvss_score': max(cvss_scores),
                'std_cvss_score': statistics.stdev(cvss_scores) if len(cvss_scores) > 1 else 0
            })
        
        if risk_scores:
            features.update({
                'avg_risk_score': statistics.mean(risk_scores),
                'median_risk_score': statistics.median(risk_scores),
                'max_risk_score': max(risk_scores)
            })
        
        return features
    
    def _calculate_diversity_index(self, counter: Counter) -> float:
        """Calculate Shannon diversity index"""
        if not counter:
            return 0.0
        
        total = sum(counter.values())
        entropy = 0.0
        
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _calculate_severity_score(self, severity_counts: Counter) -> float:
        """Calculate weighted severity score"""
        weights = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'INFO': 0}
        
        total_score = 0
        total_count = 0
        
        for severity, count in severity_counts.items():
            weight = weights.get(severity.upper(), 1)
            total_score += weight * count
            total_count += count
        
        return total_score / total_count if total_count > 0 else 0
    
    async def train_anomaly_model(self, historical_data_days: Optional[int] = None) -> Optional[MLModelMetrics]:
        """Train IsolationForest on real scan history (activation-gated, spec 5.1 P4)."""
        from config import settings
        days = historical_data_days or settings.ml_training_window_days

        if not settings.ml_isolation_forest_enabled:
            logger.info("IsolationForest training skipped: ML_ISOLATION_FOREST_ENABLED=false")
            return None

        training_features = await self._collect_training_data(days)
        if len(training_features) < settings.ml_min_training_scans:
            logger.warning(
                "Insufficient scan history for IsolationForest: %d < %d",
                len(training_features), settings.ml_min_training_scans,
            )
            return None

        feature_matrix, feature_names = self._prepare_feature_matrix(training_features)

        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            logger.error("scikit-learn not installed; cannot train IsolationForest: %s", e)
            return None

        scaler = StandardScaler()
        scaled = scaler.fit_transform(feature_matrix)
        model = IsolationForest(contamination=0.1, random_state=42)
        predictions = model.fit_predict(scaled)
        scores = model.decision_function(scaled)

        anomaly_rate = float((predictions == -1).sum()) / len(predictions)
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            importances = [0.0] * len(feature_names)

        model_id = f"anomaly_model_{utc_now().strftime('%Y%m%d_%H%M%S')}"
        metrics = MLModelMetrics(
            model_id=model_id,
            model_type="IsolationForest",
            training_data_size=len(training_features),
            anomaly_rate=round(anomaly_rate, 4),
            score_mean=round(float(scores.mean()), 4),
            score_std=round(float(scores.std()), 4),
            last_trained=utc_now().isoformat(),
            feature_importance=dict(zip(feature_names, [round(float(v), 4) for v in importances])),
        )

        self.models_path.mkdir(parents=True, exist_ok=True)
        model_file = self.models_path / f"{model_id}.pkl"
        with open(model_file, "wb") as f:
            pickle.dump({"model": model, "scaler": scaler, "features": feature_names}, f)

        await self._store_model_metrics(metrics, str(model_file.resolve()))
        self.models["anomaly_detector"] = {
            "model": model, "scaler": scaler, "features": feature_names, "metrics": metrics,
        }
        logger.info(
            "IsolationForest trained on %d scans (anomaly_rate=%.2f%%)",
            len(training_features), anomaly_rate * 100,
        )
        return metrics
    
    async def _collect_training_data(self, days: int) -> List[Dict[str, Any]]:
        """One feature vector per completed scan in the window (REAL data, A10)."""
        from models.base import ScanStatus
        from models.report import ScanReport

        cutoff = utc_now() - timedelta(days=days)
        try:
            reports = await ScanReport.find(
                ScanReport.started_at >= cutoff,
                ScanReport.status == ScanStatus.COMPLETED,
            ).to_list()
        except Exception as e:
            logger.error("Failed to load scan history for ML training: %s", e)
            return []

        rows: List[Dict[str, Any]] = []
        for rep in reports:
            findings = [f for sr in rep.scan_results for f in (sr.findings or [])]
            total = len(findings)
            if total == 0:
                continue

            def _sev(f):
                s = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
                return s.lower()

            crit = sum(1 for f in findings if _sev(f) == "critical")
            high = sum(1 for f in findings if _sev(f) == "high")
            cvss_vals = [
                f.cvss_score.base_score
                for f in findings
                if f.cvss_score and f.cvss_score.base_score
            ]
            cwes = {f.cwe_id for f in findings if f.cwe_id}
            hours = max((rep.duration_seconds or 3600.0) / 3600.0, 0.1)
            rows.append({
                "scan_id": rep.scan_id,
                "total_findings": total,
                "critical_ratio": crit / total,
                "high_ratio": high / total,
                "avg_cvss_score": (sum(cvss_vals) / len(cvss_vals)) if cvss_vals else 0.0,
                "unique_cwe_count": len(cwes),
                "findings_per_hour": total / hours,
            })
        return rows
    
    def _prepare_feature_matrix(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Prepare feature matrix for ML training"""
        feature_names = list(FEATURE_NAMES)
        
        feature_matrix = []
        for data_point in training_data:
            feature_vector = [data_point.get(name, 0) for name in feature_names]
            feature_matrix.append(feature_vector)
        
        return np.array(feature_matrix), feature_names
    
    async def detect_anomalies(self, current_findings: List[Dict[str, Any]], 
                              time_period: str = "24h") -> List[AnomalyAlert]:
        """Detect anomalies in current findings"""
        logger.info(f"🔍 Analyzing {len(current_findings)} findings for anomalies")
        
        alerts = []
        
        # Extract features from current findings
        current_features = await self.extract_features_from_findings(current_findings, time_period)
        
        if not current_features:
            return alerts
        
        # Rule-based anomaly detection
        rule_based_alerts = await self._detect_rule_based_anomalies(current_features, current_findings)
        alerts.extend(rule_based_alerts)
        
        # ML-based anomaly detection (if model exists)
        if 'anomaly_detector' in self.models:
            ml_alerts = await self._detect_ml_based_anomalies(current_features)
            alerts.extend(ml_alerts)
        
        # Store alerts
        for alert in alerts:
            await self._store_anomaly_alert(alert)
        
        logger.info(f"🚨 Detected {len(alerts)} anomalies")
        return alerts
    
    async def _detect_rule_based_anomalies(self, features: Dict[str, Any], 
                                          findings: List[Dict[str, Any]]) -> List[AnomalyAlert]:
        """Detect anomalies using rule-based logic"""
        alerts = []
        
        # Spike in total findings
        total_findings = features.get('total_findings', 0)
        if total_findings > 50:  # Threshold
            alerts.append(AnomalyAlert(
                alert_id=f"spike_{utc_now().strftime('%Y%m%d_%H%M%S')}",
                anomaly_type="spike",
                finding_type="total_findings",
                severity="HIGH",
                description=f"Unusual spike in total findings: {total_findings} (normal: ~20)",
                current_value=total_findings,
                baseline_value=20.0,
                deviation_percentage=((total_findings - 20) / 20) * 100,
                confidence_score=0.9,
                timestamp=utc_now().isoformat(),
                recommended_actions=[
                    "Investigate potential security incident",
                    "Review recent deployments", 
                    "Check scanning tool configuration"
                ]
            ))
        
        # High critical ratio
        critical_ratio = features.get('critical_ratio', 0)
        if critical_ratio > 0.3:  # More than 30% critical
            alerts.append(AnomalyAlert(
                alert_id=f"critical_spike_{utc_now().strftime('%Y%m%d_%H%M%S')}",
                anomaly_type="severity_spike",
                finding_type="critical_vulnerabilities",
                severity="CRITICAL",
                description=f"Unusual proportion of critical findings: {critical_ratio:.1%} (normal: ~10%)",
                current_value=critical_ratio,
                baseline_value=0.1,
                deviation_percentage=((critical_ratio - 0.1) / 0.1) * 100,
                confidence_score=0.95,
                timestamp=utc_now().isoformat(),
                recommended_actions=[
                    "Immediate security team escalation",
                    "Block deployments until review",
                    "Prioritize critical vulnerability remediation"
                ]
            ))
        
        # New CWE types
        cwe_counts = Counter([f.get('cwe_id') for f in findings if f.get('cwe_id')])
        rare_cwes = [cwe for cwe, count in cwe_counts.items() if count == 1 and cwe not in ['79', '89', '22']]
        
        if rare_cwes:
            alerts.append(AnomalyAlert(
                alert_id=f"new_cwe_{utc_now().strftime('%Y%m%d_%H%M%S')}",
                anomaly_type="new_pattern",
                finding_type="cwe_types",
                severity="MEDIUM",
                description=f"New/rare CWE types detected: {', '.join(rare_cwes)}",
                current_value=len(rare_cwes),
                baseline_value=0.0,
                deviation_percentage=100.0,
                confidence_score=0.8,
                timestamp=utc_now().isoformat(),
                recommended_actions=[
                    "Research new vulnerability types",
                    "Update security training materials",
                    "Review detection rules"
                ]
            ))
        
        return alerts
    
    async def _detect_ml_based_anomalies(self, features: Dict[str, Any]) -> List[AnomalyAlert]:
        """Detect anomalies using trained ML model"""
        alerts = []
        
        try:
            model_data = self.models['anomaly_detector']
            model = model_data['model']
            scaler = model_data['scaler']
            feature_names = model_data['features']
            
            # Prepare feature vector
            feature_vector = [features.get(name, 0) for name in feature_names]
            scaled_vector = scaler.transform([feature_vector])
            
            # Predict anomaly
            prediction = model.predict(scaled_vector)[0]
            anomaly_score = model.decision_function(scaled_vector)[0]
            
            if prediction == -1:  # Anomaly detected
                alerts.append(AnomalyAlert(
                    alert_id=f"ml_anomaly_{utc_now().strftime('%Y%m%d_%H%M%S')}",
                    anomaly_type="ml_detected",
                    finding_type="pattern_anomaly", 
                    severity="MEDIUM",
                    description=f"ML model detected anomalous pattern (score: {anomaly_score:.3f})",
                    current_value=anomaly_score,
                    baseline_value=0.0,
                    deviation_percentage=abs(anomaly_score) * 100,
                    confidence_score=min(abs(anomaly_score), 1.0),
                    timestamp=utc_now().isoformat(),
                    recommended_actions=[
                        "Review finding patterns for unusual activity",
                        "Validate with security team",
                        "Check for potential security incidents"
                    ]
                ))
        
        except Exception as e:
            logger.error(f"❌ ML anomaly detection failed: {e}")
        
        return alerts
    
    async def _store_model_metrics(self, metrics: MLModelMetrics, model_file_path: str):
        """Store ML model metrics in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ml_models
            (model_id, model_type, training_data_size, accuracy, precision_score,
             recall_score, f1_score, last_trained, feature_importance_json,
             model_file_path, status, anomaly_rate, score_mean, score_std)
            VALUES (?, ?, ?, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.model_id, metrics.model_type, metrics.training_data_size,
            metrics.last_trained, json.dumps(metrics.feature_importance),
            model_file_path, 'active',
            metrics.anomaly_rate, metrics.score_mean, metrics.score_std,
        ))
        
        conn.commit()
        conn.close()
    
    async def _store_anomaly_alert(self, alert: AnomalyAlert):
        """Store anomaly alert in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO anomaly_alerts
            (alert_id, anomaly_type, finding_type, severity, description,
             current_value, baseline_value, deviation_percentage, confidence_score,
             timestamp, recommended_actions_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.alert_id, alert.anomaly_type, alert.finding_type, alert.severity,
            alert.description, alert.current_value, alert.baseline_value,
            alert.deviation_percentage, alert.confidence_score, alert.timestamp,
            json.dumps(alert.recommended_actions)
        ))
        
        conn.commit()
        conn.close()
    
    async def get_anomaly_dashboard(self) -> Dict[str, Any]:
        """Generate anomaly detection dashboard (degrades on legacy schema)."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent alerts
            cursor.execute('''
                SELECT * FROM anomaly_alerts
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''')
            recent_alerts = cursor.fetchall()

            # Get alert statistics
            cursor.execute('''
                SELECT severity, COUNT(*) FROM anomaly_alerts
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY severity
            ''')
            alert_stats = dict(cursor.fetchall())

            # Get active model (honest metrics columns)
            cursor.execute('''
                SELECT model_id, model_type, training_data_size, last_trained,
                       anomaly_rate, score_mean, score_std
                FROM ml_models WHERE status = 'active'
                ORDER BY last_trained DESC LIMIT 1
            ''')
            active_model = cursor.fetchone()

            conn.close()
        except sqlite3.Error as e:
            logger.error("Anomaly dashboard query failed (legacy schema?): %s", e)
            if conn is not None:
                conn.close()
            return {
                "recent_alerts": [],
                "alert_statistics": {},
                "active_model": None,
                "total_recent_alerts": 0,
                "anomaly_detection_status": "degraded",
                "error": str(e),
            }

        dashboard = {
            "recent_alerts": [
                {
                    "alert_id": row[0],
                    "anomaly_type": row[1],
                    "severity": row[3],
                    "description": row[4],
                    "timestamp": row[9]
                }
                for row in recent_alerts[:10]
            ],
            "alert_statistics": alert_stats,
            "active_model": {
                "model_id": active_model[0],
                "model_type": active_model[1],
                "training_data_size": active_model[2],
                "last_trained": active_model[3],
                "anomaly_rate": active_model[4],
                "score_mean": active_model[5],
                "score_std": active_model[6],
            } if active_model else None,
            "total_recent_alerts": len(recent_alerts),
            "anomaly_detection_status": "active" if 'anomaly_detector' in self.models else "training_required"
        }
        
        return dashboard


_engine: Optional[MLAnomalyDetectionEngine] = None


def get_ml_engine() -> MLAnomalyDetectionEngine:
    """Lazy singleton: no sqlite/mkdir side effects until first use."""
    global _engine
    if _engine is None:
        _engine = MLAnomalyDetectionEngine()
    return _engine

"""
SBOM (Software Bill of Materials) Generation Service
Generates SPDX and CycloneDX format SBOMs for supply chain security
Enterprise-grade compliance with industry standards
"""
import asyncio
import json
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class SBOMFormat(Enum):
    """SBOM output formats"""
    SPDX_JSON = "spdx-json"
    SPDX_TAG_VALUE = "spdx-tv"
    CYCLONEDX_JSON = "cyclonedx-json"
    CYCLONEDX_XML = "cyclonedx-xml"


class ComponentType(Enum):
    """Component types in SBOM"""
    APPLICATION = "application"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    CONTAINER = "container"
    OPERATING_SYSTEM = "operating-system"
    DEVICE = "device"
    FIRMWARE = "firmware"
    FILE = "file"
    DATA = "data"


class LicenseType(Enum):
    """Common open source licenses"""
    MIT = "MIT"
    APACHE_2 = "Apache-2.0"
    GPL_2 = "GPL-2.0"
    GPL_3 = "GPL-3.0"
    BSD_2 = "BSD-2-Clause"
    BSD_3 = "BSD-3-Clause"
    LGPL_2_1 = "LGPL-2.1"
    LGPL_3 = "LGPL-3.0"
    MPL_2 = "MPL-2.0"
    ISC = "ISC"
    UNLICENSED = "UNLICENSED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ComponentHash:
    """Hash information for component verification"""
    algorithm: str  # SHA-256, SHA-512, MD5, etc.
    value: str


@dataclass
class ExternalReference:
    """External reference for a component"""
    type: str  # vcs, website, documentation, etc.
    url: str
    comment: Optional[str] = None


@dataclass 
class Vulnerability:
    """Vulnerability associated with a component"""
    id: str  # CVE-XXXX-XXXXX
    source: str  # NVD, OSV, etc.
    severity: str
    cvss_score: Optional[float] = None
    description: Optional[str] = None
    fix_version: Optional[str] = None


@dataclass
class Component:
    """SBOM Component (dependency/package)"""
    bom_ref: str
    type: ComponentType
    name: str
    version: str
    purl: Optional[str] = None  # Package URL
    cpe: Optional[str] = None   # Common Platform Enumeration
    description: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    group: Optional[str] = None
    scope: Optional[str] = None  # required, optional, excluded
    licenses: List[str] = field(default_factory=list)
    hashes: List[ComponentHash] = field(default_factory=list)
    external_references: List[ExternalReference] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # bom-refs of deps


@dataclass
class SBOMMetadata:
    """SBOM document metadata"""
    timestamp: datetime
    tools: List[Dict[str, str]]
    authors: List[Dict[str, str]]
    component: Optional[Component] = None  # Main/root component
    manufacture: Optional[Dict[str, str]] = None
    supplier: Optional[Dict[str, str]] = None


@dataclass
class SBOM:
    """Software Bill of Materials"""
    bom_format: str
    spec_version: str
    serial_number: str
    version: int
    metadata: SBOMMetadata
    components: List[Component]
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    compositions: List[Dict[str, Any]] = field(default_factory=list)
    external_references: List[ExternalReference] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)


class SBOMGeneratorService:
    """
    SBOM Generation Service
    Generates Software Bill of Materials in SPDX and CycloneDX formats
    for supply chain security and compliance requirements.
    """

    CYCLONEDX_VERSION = "1.5"
    SPDX_VERSION = "SPDX-2.3"
    TOOL_NAME = "ONYX-Platform"
    TOOL_VERSION = "1.0.0"
    TOOL_VENDOR = "ONYX"

    def __init__(self):
        self._package_parsers = {
            "package.json": self._parse_npm_packages,
            "package-lock.json": self._parse_npm_lock,
            "requirements.txt": self._parse_python_requirements,
            "Pipfile.lock": self._parse_pipfile_lock,
            "poetry.lock": self._parse_poetry_lock,
            "pom.xml": self._parse_maven_pom,
            "build.gradle": self._parse_gradle,
            "Gemfile.lock": self._parse_gemfile_lock,
            "go.mod": self._parse_go_mod,
            "Cargo.lock": self._parse_cargo_lock,
            "composer.lock": self._parse_composer_lock,
        }

    async def generate_sbom(
        self,
        project_path: str,
        project_name: str,
        project_version: str = "1.0.0",
        output_format: SBOMFormat = SBOMFormat.CYCLONEDX_JSON,
        include_vulnerabilities: bool = True,
        include_licenses: bool = True
    ) -> Dict[str, Any]:
        """
        Generate SBOM for a project.
        
        Args:
            project_path: Path to project root
            project_name: Name of the project
            project_version: Version of the project
            output_format: Output format (SPDX or CycloneDX)
            include_vulnerabilities: Include known vulnerabilities
            include_licenses: Include license information
            
        Returns:
            SBOM document as dictionary
        """
        logger.info(f"Generating SBOM for {project_name} in {output_format.value} format")
        
        # Discover and parse all dependency files
        components = await self._discover_components(project_path)
        
        # Enrich with vulnerability data if requested
        if include_vulnerabilities:
            components = await self._enrich_vulnerabilities(components)
        
        # Enrich with license data if requested
        if include_licenses:
            components = await self._enrich_licenses(components)
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(components)
        
        # Create SBOM document
        sbom = self._create_sbom(
            project_name=project_name,
            project_version=project_version,
            components=components,
            dependencies=dependencies
        )
        
        # Convert to requested format
        if output_format in [SBOMFormat.CYCLONEDX_JSON, SBOMFormat.CYCLONEDX_XML]:
            return self._to_cyclonedx(sbom, output_format)
        else:
            return self._to_spdx(sbom, output_format)

    async def generate_from_scan_results(
        self,
        scan_results: Dict[str, Any],
        project_name: str,
        output_format: SBOMFormat = SBOMFormat.CYCLONEDX_JSON
    ) -> Dict[str, Any]:
        """
        Generate SBOM from scan results.
        
        Args:
            scan_results: Security scan results containing dependency info
            project_name: Name of the project
            output_format: Output format
            
        Returns:
            SBOM document
        """
        components = []
        
        # Extract components from Trivy results
        trivy_results = scan_results.get("trivy", {})
        if trivy_results:
            components.extend(self._extract_trivy_components(trivy_results))
        
        # Extract from Safety results (Python)
        safety_results = scan_results.get("safety", {})
        if safety_results:
            components.extend(self._extract_safety_components(safety_results))
        
        # Extract from npm audit results
        npm_results = scan_results.get("npm_audit", {})
        if npm_results:
            components.extend(self._extract_npm_components(npm_results))
        
        # Deduplicate components
        components = self._deduplicate_components(components)
        
        # Create SBOM
        sbom = self._create_sbom(
            project_name=project_name,
            project_version="scan-derived",
            components=components,
            dependencies=[]
        )
        
        if output_format in [SBOMFormat.CYCLONEDX_JSON, SBOMFormat.CYCLONEDX_XML]:
            return self._to_cyclonedx(sbom, output_format)
        else:
            return self._to_spdx(sbom, output_format)

    async def _discover_components(self, project_path: str) -> List[Component]:
        """Discover all components in a project"""
        components = []
        path = Path(project_path)
        
        for filename, parser in self._package_parsers.items():
            # Search for dependency files
            for dep_file in path.rglob(filename):
                # Skip node_modules, venv, etc.
                if any(p in str(dep_file) for p in ["node_modules", "venv", ".venv", "__pycache__", "target"]):
                    continue
                    
                try:
                    parsed = await parser(dep_file)
                    components.extend(parsed)
                except Exception as e:
                    logger.warning(f"Failed to parse {dep_file}: {e}")
        
        return self._deduplicate_components(components)

    async def _parse_npm_packages(self, filepath: Path) -> List[Component]:
        """Parse package.json"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Dependencies
        for name, version in data.get("dependencies", {}).items():
            components.append(self._create_npm_component(name, version, "required"))
        
        # Dev dependencies
        for name, version in data.get("devDependencies", {}).items():
            components.append(self._create_npm_component(name, version, "optional"))
        
        return components

    async def _parse_npm_lock(self, filepath: Path) -> List[Component]:
        """Parse package-lock.json"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        packages = data.get("packages", data.get("dependencies", {}))
        
        for pkg_path, pkg_info in packages.items():
            if not pkg_path or pkg_path == "":
                continue
            
            name = pkg_path.replace("node_modules/", "").split("/")[-1]
            version = pkg_info.get("version", "unknown")
            
            components.append(self._create_npm_component(
                name, 
                version,
                "optional" if pkg_info.get("dev") else "required"
            ))
        
        return components

    async def _parse_python_requirements(self, filepath: Path) -> List[Component]:
        """Parse requirements.txt"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                
                # Parse package==version or package>=version
                match = re.match(r"([a-zA-Z0-9_-]+)\s*([<>=!~]+)?\s*([0-9.]+)?", line)
                if match:
                    name = match.group(1)
                    version = match.group(3) or "latest"
                    components.append(self._create_pypi_component(name, version))
        
        return components

    async def _parse_pipfile_lock(self, filepath: Path) -> List[Component]:
        """Parse Pipfile.lock"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for section in ["default", "develop"]:
            for name, info in data.get(section, {}).items():
                version = info.get("version", "").lstrip("=")
                scope = "optional" if section == "develop" else "required"
                components.append(self._create_pypi_component(name, version, scope))
        
        return components

    async def _parse_poetry_lock(self, filepath: Path) -> List[Component]:
        """Parse poetry.lock (TOML format)"""
        components = []
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        with open(filepath, 'rb') as f:
            data = tomllib.load(f)
        
        for package in data.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")
            components.append(self._create_pypi_component(name, version))
        
        return components

    async def _parse_maven_pom(self, filepath: Path) -> List[Component]:
        """Parse pom.xml"""
        components = []
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Handle namespace
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            
            for dep in root.findall(".//m:dependency", ns) + root.findall(".//dependency"):
                group_id = dep.findtext("m:groupId", "", ns) or dep.findtext("groupId", "")
                artifact_id = dep.findtext("m:artifactId", "", ns) or dep.findtext("artifactId", "")
                version = dep.findtext("m:version", "", ns) or dep.findtext("version", "")
                scope = dep.findtext("m:scope", "compile", ns) or dep.findtext("scope", "compile")
                
                if artifact_id:
                    components.append(self._create_maven_component(group_id, artifact_id, version, scope))
        except Exception as e:
            logger.warning(f"Failed to parse Maven POM: {e}")
        
        return components

    async def _parse_gradle(self, filepath: Path) -> List[Component]:
        """Parse build.gradle (basic parsing)"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match implementation/compile dependencies
        patterns = [
            r"implementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
            r"compile\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
            r"api\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                group_id, artifact_id, version = match.groups()
                components.append(self._create_maven_component(group_id, artifact_id, version))
        
        return components

    async def _parse_gemfile_lock(self, filepath: Path) -> List[Component]:
        """Parse Gemfile.lock"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            in_specs = False
            for line in f:
                if line.strip() == "specs:":
                    in_specs = True
                    continue
                
                if in_specs:
                    match = re.match(r"\s+(\S+)\s+\(([^)]+)\)", line)
                    if match:
                        name, version = match.groups()
                        components.append(self._create_rubygems_component(name, version))
                    elif not line.startswith(" "):
                        in_specs = False
        
        return components

    async def _parse_go_mod(self, filepath: Path) -> List[Component]:
        """Parse go.mod"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            in_require = False
            for line in f:
                line = line.strip()
                
                if line.startswith("require ("):
                    in_require = True
                    continue
                elif line == ")":
                    in_require = False
                    continue
                
                if in_require or line.startswith("require "):
                    match = re.match(r"(?:require\s+)?(\S+)\s+(\S+)", line)
                    if match:
                        module, version = match.groups()
                        components.append(self._create_go_component(module, version))
        
        return components

    async def _parse_cargo_lock(self, filepath: Path) -> List[Component]:
        """Parse Cargo.lock"""
        components = []
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        with open(filepath, 'rb') as f:
            data = tomllib.load(f)
        
        for package in data.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")
            components.append(self._create_cargo_component(name, version))
        
        return components

    async def _parse_composer_lock(self, filepath: Path) -> List[Component]:
        """Parse composer.lock"""
        components = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for pkg in data.get("packages", []) + data.get("packages-dev", []):
            name = pkg.get("name", "")
            version = pkg.get("version", "").lstrip("v")
            components.append(self._create_packagist_component(name, version))
        
        return components

    def _create_npm_component(self, name: str, version: str, scope: str = "required") -> Component:
        """Create NPM component"""
        version = version.lstrip("^~>=<")
        return Component(
            bom_ref=f"pkg:npm/{name}@{version}",
            type=ComponentType.LIBRARY,
            name=name,
            version=version,
            purl=f"pkg:npm/{name}@{version}",
            scope=scope
        )

    def _create_pypi_component(self, name: str, version: str, scope: str = "required") -> Component:
        """Create PyPI component"""
        return Component(
            bom_ref=f"pkg:pypi/{name}@{version}",
            type=ComponentType.LIBRARY,
            name=name,
            version=version,
            purl=f"pkg:pypi/{name}@{version}",
            scope=scope
        )

    def _create_maven_component(self, group_id: str, artifact_id: str, version: str, scope: str = "required") -> Component:
        """Create Maven component"""
        return Component(
            bom_ref=f"pkg:maven/{group_id}/{artifact_id}@{version}",
            type=ComponentType.LIBRARY,
            name=artifact_id,
            version=version,
            group=group_id,
            purl=f"pkg:maven/{group_id}/{artifact_id}@{version}",
            scope=scope
        )

    def _create_rubygems_component(self, name: str, version: str) -> Component:
        """Create RubyGems component"""
        return Component(
            bom_ref=f"pkg:gem/{name}@{version}",
            type=ComponentType.LIBRARY,
            name=name,
            version=version,
            purl=f"pkg:gem/{name}@{version}"
        )

    def _create_go_component(self, module: str, version: str) -> Component:
        """Create Go module component"""
        return Component(
            bom_ref=f"pkg:golang/{module}@{version}",
            type=ComponentType.LIBRARY,
            name=module,
            version=version,
            purl=f"pkg:golang/{module}@{version}"
        )

    def _create_cargo_component(self, name: str, version: str) -> Component:
        """Create Cargo/Rust component"""
        return Component(
            bom_ref=f"pkg:cargo/{name}@{version}",
            type=ComponentType.LIBRARY,
            name=name,
            version=version,
            purl=f"pkg:cargo/{name}@{version}"
        )

    def _create_packagist_component(self, name: str, version: str) -> Component:
        """Create Packagist/PHP component"""
        return Component(
            bom_ref=f"pkg:composer/{name}@{version}",
            type=ComponentType.LIBRARY,
            name=name,
            version=version,
            purl=f"pkg:composer/{name}@{version}"
        )

    def _deduplicate_components(self, components: List[Component]) -> List[Component]:
        """Deduplicate components by purl"""
        seen = {}
        for comp in components:
            key = comp.purl or f"{comp.name}@{comp.version}"
            if key not in seen:
                seen[key] = comp
            else:
                # Merge vulnerabilities and licenses
                existing = seen[key]
                existing.vulnerabilities.extend(comp.vulnerabilities)
                existing.licenses = list(set(existing.licenses + comp.licenses))
        return list(seen.values())

    async def _enrich_vulnerabilities(self, components: List[Component]) -> List[Component]:
        """Enrich components with vulnerability data from OSV/NVD"""
        try:
            from services.infrastructure.osv_nvd_integration import get_osv_nvd_service, PackageQuery, Ecosystem
            
            service = await get_osv_nvd_service()
            
            for comp in components:
                # Map purl to ecosystem
                ecosystem = self._purl_to_ecosystem(comp.purl)
                if not ecosystem:
                    continue
                
                query = PackageQuery(
                    name=comp.name,
                    version=comp.version,
                    ecosystem=ecosystem
                )
                
                vulns = await service.query_osv(query)
                
                for vuln in vulns:
                    comp.vulnerabilities.append(Vulnerability(
                        id=vuln.id,
                        source=vuln.source.value,
                        severity=vuln.severity,
                        cvss_score=vuln.cvss_score,
                        description=vuln.summary,
                        fix_version=vuln.fixed_versions[0] if vuln.fixed_versions else None
                    ))
                    
        except Exception as e:
            logger.warning(f"Failed to enrich vulnerabilities: {e}")
        
        return components

    async def _enrich_licenses(self, components: List[Component]) -> List[Component]:
        """Enrich components with license data"""
        # This would typically query package registries for license info
        # For now, we'll leave licenses as parsed from lock files
        return components

    def _purl_to_ecosystem(self, purl: Optional[str]) -> Optional["Ecosystem"]:
        """Convert Package URL to OSV ecosystem"""
        from services.infrastructure.osv_nvd_integration import Ecosystem
        
        if not purl:
            return None
        
        ecosystem_map = {
            "pkg:npm/": Ecosystem.NPM,
            "pkg:pypi/": Ecosystem.PYPI,
            "pkg:maven/": Ecosystem.MAVEN,
            "pkg:golang/": Ecosystem.GO,
            "pkg:gem/": Ecosystem.RUBYGEMS,
            "pkg:cargo/": Ecosystem.CARGO,
            "pkg:composer/": Ecosystem.PACKAGIST,
        }
        
        for prefix, ecosystem in ecosystem_map.items():
            if purl.startswith(prefix):
                return ecosystem
        
        return None

    def _build_dependency_graph(self, components: List[Component]) -> List[Dict[str, Any]]:
        """Build dependency graph for SBOM"""
        # For now, return simple structure
        # Full implementation would parse lock files for transitive deps
        return [
            {"ref": comp.bom_ref, "dependsOn": comp.dependencies}
            for comp in components
            if comp.dependencies
        ]

    def _create_sbom(
        self,
        project_name: str,
        project_version: str,
        components: List[Component],
        dependencies: List[Dict[str, Any]]
    ) -> SBOM:
        """Create SBOM document"""
        serial = f"urn:uuid:{uuid.uuid4()}"
        
        metadata = SBOMMetadata(
            timestamp=datetime.now(timezone.utc),
            tools=[{
                "vendor": self.TOOL_VENDOR,
                "name": self.TOOL_NAME,
                "version": self.TOOL_VERSION
            }],
            authors=[{
                "name": "ONYX Platform",
                "email": "security@onyx-security.ai"
            }],
            component=Component(
                bom_ref=f"pkg:generic/{project_name}@{project_version}",
                type=ComponentType.APPLICATION,
                name=project_name,
                version=project_version
            )
        )
        
        return SBOM(
            bom_format="CycloneDX",
            spec_version=self.CYCLONEDX_VERSION,
            serial_number=serial,
            version=1,
            metadata=metadata,
            components=components,
            dependencies=dependencies
        )

    def _to_cyclonedx(self, sbom: SBOM, format: SBOMFormat) -> Dict[str, Any]:
        """Convert SBOM to CycloneDX format"""
        doc = {
            "bomFormat": "CycloneDX",
            "specVersion": self.CYCLONEDX_VERSION,
            "serialNumber": sbom.serial_number,
            "version": sbom.version,
            "metadata": {
                "timestamp": sbom.metadata.timestamp.isoformat(),
                "tools": sbom.metadata.tools,
                "authors": sbom.metadata.authors,
                "component": self._component_to_dict(sbom.metadata.component) if sbom.metadata.component else None
            },
            "components": [
                self._component_to_dict(comp) for comp in sbom.components
            ],
            "dependencies": sbom.dependencies,
            "vulnerabilities": [
                vuln for comp in sbom.components 
                for vuln in self._vulnerabilities_to_list(comp)
            ]
        }
        
        return doc

    def _to_spdx(self, sbom: SBOM, format: SBOMFormat) -> Dict[str, Any]:
        """Convert SBOM to SPDX format"""
        doc = {
            "spdxVersion": self.SPDX_VERSION,
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": sbom.metadata.component.name if sbom.metadata.component else "unknown",
            "documentNamespace": sbom.serial_number,
            "creationInfo": {
                "created": sbom.metadata.timestamp.isoformat(),
                "creators": [
                    f"Tool: {tool['name']}-{tool['version']}" 
                    for tool in sbom.metadata.tools
                ]
            },
            "packages": [
                self._component_to_spdx_package(comp, idx)
                for idx, comp in enumerate(sbom.components)
            ],
            "relationships": [
                {
                    "spdxElementId": "SPDXRef-DOCUMENT",
                    "relatedSpdxElement": f"SPDXRef-Package-{idx}",
                    "relationshipType": "DESCRIBES"
                }
                for idx in range(len(sbom.components))
            ]
        }
        
        return doc

    def _component_to_dict(self, comp: Component) -> Dict[str, Any]:
        """Convert component to CycloneDX dict"""
        result = {
            "bom-ref": comp.bom_ref,
            "type": comp.type.value,
            "name": comp.name,
            "version": comp.version
        }
        
        if comp.purl:
            result["purl"] = comp.purl
        if comp.group:
            result["group"] = comp.group
        if comp.description:
            result["description"] = comp.description
        if comp.licenses:
            result["licenses"] = [{"license": {"id": lic}} for lic in comp.licenses]
        if comp.scope:
            result["scope"] = comp.scope
        if comp.hashes:
            result["hashes"] = [
                {"alg": h.algorithm, "content": h.value}
                for h in comp.hashes
            ]
        
        return result

    def _component_to_spdx_package(self, comp: Component, idx: int) -> Dict[str, Any]:
        """Convert component to SPDX package"""
        return {
            "SPDXID": f"SPDXRef-Package-{idx}",
            "name": comp.name,
            "versionInfo": comp.version,
            "downloadLocation": comp.purl or "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": comp.licenses[0] if comp.licenses else "NOASSERTION",
            "licenseDeclared": comp.licenses[0] if comp.licenses else "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": comp.purl
                }
            ] if comp.purl else []
        }

    def _vulnerabilities_to_list(self, comp: Component) -> List[Dict[str, Any]]:
        """Convert component vulnerabilities to CycloneDX format"""
        return [
            {
                "id": vuln.id,
                "source": {"name": vuln.source},
                "ratings": [{
                    "severity": vuln.severity,
                    "score": vuln.cvss_score
                }] if vuln.cvss_score else [],
                "description": vuln.description or "",
                "affects": [{
                    "ref": comp.bom_ref,
                    "versions": [{"version": comp.version}]
                }],
                "recommendation": f"Upgrade to {vuln.fix_version}" if vuln.fix_version else None
            }
            for vuln in comp.vulnerabilities
        ]

    def _extract_trivy_components(self, trivy_results: Dict) -> List[Component]:
        """Extract components from Trivy scan results"""
        components = []
        
        for result in trivy_results.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                purl = vuln.get("PkgID", "")
                name = vuln.get("PkgName", "")
                version = vuln.get("InstalledVersion", "")
                
                if name and version:
                    comp = Component(
                        bom_ref=purl or f"pkg:generic/{name}@{version}",
                        type=ComponentType.LIBRARY,
                        name=name,
                        version=version,
                        purl=purl
                    )
                    
                    comp.vulnerabilities.append(Vulnerability(
                        id=vuln.get("VulnerabilityID", ""),
                        source="trivy",
                        severity=vuln.get("Severity", "").lower(),
                        cvss_score=vuln.get("CVSS", {}).get("nvd", {}).get("V3Score"),
                        description=vuln.get("Description"),
                        fix_version=vuln.get("FixedVersion")
                    ))
                    
                    components.append(comp)
        
        return components

    def _extract_safety_components(self, safety_results: Dict) -> List[Component]:
        """Extract components from Safety scan results"""
        components = []
        
        for vuln in safety_results.get("vulnerabilities", []):
            name = vuln.get("package_name", "")
            version = vuln.get("analyzed_version", "")
            
            if name and version:
                comp = Component(
                    bom_ref=f"pkg:pypi/{name}@{version}",
                    type=ComponentType.LIBRARY,
                    name=name,
                    version=version,
                    purl=f"pkg:pypi/{name}@{version}"
                )
                
                comp.vulnerabilities.append(Vulnerability(
                    id=vuln.get("vulnerability_id", ""),
                    source="safety",
                    severity=vuln.get("severity", "unknown").lower(),
                    description=vuln.get("advisory")
                ))
                
                components.append(comp)
        
        return components

    def _extract_npm_components(self, npm_results: Dict) -> List[Component]:
        """Extract components from npm audit results"""
        components = []
        
        for vuln in npm_results.get("vulnerabilities", {}).values():
            name = vuln.get("name", "")
            version = vuln.get("range", "")
            
            if name:
                comp = Component(
                    bom_ref=f"pkg:npm/{name}@{version}",
                    type=ComponentType.LIBRARY,
                    name=name,
                    version=version,
                    purl=f"pkg:npm/{name}@{version}"
                )
                
                comp.vulnerabilities.append(Vulnerability(
                    id=str(vuln.get("via", [{}])[0].get("source", "")),
                    source="npm",
                    severity=vuln.get("severity", "").lower(),
                    fix_version=vuln.get("fixAvailable", {}).get("version")
                ))
                
                components.append(comp)
        
        return components


# Singleton instance
_sbom_service: Optional[SBOMGeneratorService] = None


def get_sbom_service() -> SBOMGeneratorService:
    """Get SBOM generator service instance"""
    global _sbom_service
    if _sbom_service is None:
        _sbom_service = SBOMGeneratorService()
    return _sbom_service

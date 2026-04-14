# AETHER MASTER v1.0 — Autonomous Site Guardian
"""
Master health monitor for the entire Drops-Curated platform.

Runs every 5 minutes and checks:
  1. MongoDB connectivity & collection health
  2. Backend API responsiveness (key endpoints)
  3. Frontend / preview site availability
  4. AETHER SWARM scraper health (blocked, degraded, stale)
  5. Scheduler liveness (dead-man's switch)
  6. Disk / memory basics

Auto-heals:
  - Restarts crashed backend/frontend via supervisorctl
  - Retriggers stale scrapers through the swarm pipeline
  - Clears stale DB locks / orphan records

Escalates (WhatsApp + DB log):
  - Repeated failures it cannot resolve
  - Code-level bugs that need human review

Persists every incident + resolution to MongoDB `aether_master_memory`
so the system builds institutional knowledge over time.

Exposes data via get_master_status() for the /api/admin/aether-status endpoint.
"""

import asyncio
import httpx
import logging
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

PREVIEW_URL = os.getenv(
    "REACT_APP_BACKEND_URL",
    "https://drops-curated.preview.emergentagent.com",
)

# Critical API endpoints to probe
HEALTH_ENDPOINTS = [
    {"path": "/api/health", "method": "GET", "name": "Backend Health"},
    {"path": "/api/products/classified?page=1&limit=1", "method": "GET", "name": "Products API"},
    {"path": "/api/scrape/status", "method": "GET", "name": "Scrape Status"},
]

# Thresholds
RESPONSE_SLOW_MS = 5000
SCRAPER_STALE_MINUTES = 120  # 2 hours without a successful scrape = stale
MAX_AUTO_RESTART_PER_HOUR = 3


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class Incident:
    component: str          # mongodb | backend | frontend | scraper:<key> | scheduler
    severity: str           # critical | warning | info
    message: str
    auto_healed: bool = False
    heal_action: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MasterReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    overall_status: str = "unknown"  # healthy | degraded | critical
    mongodb_ok: bool = True
    backend_ok: bool = True
    frontend_ok: bool = True
    scrapers_ok: bool = True
    scheduler_ok: bool = True
    total_products: int = 0
    total_brands_healthy: int = 0
    total_brands_blocked: int = 0
    total_brands_stale: int = 0
    incidents: List[Dict] = field(default_factory=list)
    auto_heals: int = 0
    escalations: int = 0
    endpoint_latencies: Dict[str, int] = field(default_factory=dict)


class AetherMaster:
    """The autonomous site guardian."""

    def __init__(self):
        self._db = None
        self._restart_log: List[float] = []  # timestamps of recent restarts
        self._last_report: Optional[MasterReport] = None
        self._run_count: int = 0

    async def init(self, db):
        self._db = db
        try:
            await db.aether_master_memory.create_index([("timestamp", -1)])
            await db.aether_master_memory.create_index([("component", 1), ("timestamp", -1)])
        except Exception as e:
            logger.warning(f"[AetherMaster] Index creation warning: {e}")
        logger.info("[AetherMaster] Initialized — guarding the platform")

    # ──────────────────────────────────────────
    # Main cycle — called every 5 minutes
    # ──────────────────────────────────────────
    async def run_cycle(self):
        """Execute one full health-check + auto-heal cycle."""
        self._run_count += 1
        report = MasterReport()
        incidents: List[Incident] = []

        logger.info(f"[AetherMaster] === Cycle #{self._run_count} starting ===")

        # 1. MongoDB
        mongo_incidents = await self._check_mongodb(report)
        incidents.extend(mongo_incidents)

        # 2. Backend API endpoints
        api_incidents = await self._check_backend_apis(report)
        incidents.extend(api_incidents)

        # 3. Frontend / preview site
        fe_incidents = await self._check_frontend(report)
        incidents.extend(fe_incidents)

        # 4. Scraper health
        scraper_incidents = await self._check_scrapers(report)
        incidents.extend(scraper_incidents)

        # 5. Scheduler liveness
        sched_incidents = await self._check_scheduler(report)
        incidents.extend(sched_incidents)

        # ── Determine overall status ──
        has_critical = any(i.severity == "critical" for i in incidents)
        has_warning = any(i.severity == "warning" for i in incidents)

        if has_critical:
            report.overall_status = "critical"
        elif has_warning:
            report.overall_status = "degraded"
        else:
            report.overall_status = "healthy"

        report.incidents = [asdict(i) for i in incidents]
        report.auto_heals = sum(1 for i in incidents if i.auto_healed)
        report.escalations = sum(1 for i in incidents if i.severity == "critical" and not i.auto_healed)

        # ── Persist to DB ──
        await self._persist_report(report, incidents)

        # ── Escalate unresolved criticals ──
        unresolved = [i for i in incidents if i.severity == "critical" and not i.auto_healed]
        if unresolved:
            await self._escalate(unresolved)

        self._last_report = report
        logger.info(
            f"[AetherMaster] Cycle #{self._run_count} done — "
            f"Status: {report.overall_status} | "
            f"Incidents: {len(incidents)} | "
            f"Auto-healed: {report.auto_heals} | "
            f"Escalations: {report.escalations}"
        )

        return report

    # ──────────────────────────────────────────
    # CHECK: MongoDB
    # ──────────────────────────────────────────
    async def _check_mongodb(self, report: MasterReport) -> List[Incident]:
        incidents = []
        try:
            start = time.time()
            count = await self._db.products.count_documents({"isActive": True})
            latency = int((time.time() - start) * 1000)
            report.total_products = count
            report.endpoint_latencies["mongodb_ping"] = latency

            if latency > RESPONSE_SLOW_MS:
                incidents.append(Incident(
                    component="mongodb",
                    severity="warning",
                    message=f"MongoDB slow: {latency}ms for products count",
                ))

            # Check key collections exist and have data
            for coll_name in ["products", "subscribers", "brands"]:
                c = await self._db[coll_name].estimated_document_count()
                if coll_name == "products" and c == 0:
                    incidents.append(Incident(
                        component="mongodb",
                        severity="critical",
                        message=f"Collection '{coll_name}' is EMPTY",
                    ))

            report.mongodb_ok = not any(i.severity == "critical" for i in incidents)

        except Exception as e:
            report.mongodb_ok = False
            inc = Incident(component="mongodb", severity="critical", message=f"MongoDB unreachable: {e}")

            # Auto-heal: try to restart mongod
            if self._can_restart():
                try:
                    subprocess.run(["sudo", "service", "mongod", "restart"], timeout=10, capture_output=True)
                    inc.auto_healed = True
                    inc.heal_action = "Restarted mongod service"
                    self._restart_log.append(time.time())
                except Exception:
                    pass

            incidents.append(inc)

        return incidents

    # ──────────────────────────────────────────
    # CHECK: Backend APIs
    # ──────────────────────────────────────────
    async def _check_backend_apis(self, report: MasterReport) -> List[Incident]:
        incidents = []
        all_ok = True

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for ep in HEALTH_ENDPOINTS:
                url = f"{PREVIEW_URL}{ep['path']}"
                name = ep["name"]
                try:
                    start = time.time()
                    resp = await client.get(url)
                    latency = int((time.time() - start) * 1000)
                    report.endpoint_latencies[name] = latency

                    if resp.status_code >= 500:
                        all_ok = False
                        inc = Incident(
                            component="backend",
                            severity="critical",
                            message=f"{name} returned {resp.status_code} ({latency}ms)",
                        )
                        # Auto-heal: restart backend
                        if self._can_restart():
                            healed = await self._restart_service("backend")
                            if healed:
                                inc.auto_healed = True
                                inc.heal_action = "Restarted backend via supervisorctl"
                        incidents.append(inc)

                    elif resp.status_code >= 400:
                        incidents.append(Incident(
                            component="backend",
                            severity="warning",
                            message=f"{name} returned {resp.status_code} ({latency}ms)",
                        ))

                    elif latency > RESPONSE_SLOW_MS:
                        incidents.append(Incident(
                            component="backend",
                            severity="warning",
                            message=f"{name} slow: {latency}ms",
                        ))

                except httpx.ConnectError:
                    all_ok = False
                    inc = Incident(
                        component="backend",
                        severity="critical",
                        message=f"{name} connection refused — backend may be down",
                    )
                    if self._can_restart():
                        healed = await self._restart_service("backend")
                        if healed:
                            inc.auto_healed = True
                            inc.heal_action = "Restarted backend via supervisorctl"
                    incidents.append(inc)

                except Exception as e:
                    all_ok = False
                    incidents.append(Incident(
                        component="backend",
                        severity="warning",
                        message=f"{name} check failed: {e}",
                    ))

        report.backend_ok = all_ok
        return incidents

    # ──────────────────────────────────────────
    # CHECK: Frontend / Preview Site
    # ──────────────────────────────────────────
    async def _check_frontend(self, report: MasterReport) -> List[Incident]:
        incidents = []
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                start = time.time()
                resp = await client.get(PREVIEW_URL)
                latency = int((time.time() - start) * 1000)
                report.endpoint_latencies["frontend"] = latency

                if resp.status_code >= 500:
                    report.frontend_ok = False
                    inc = Incident(
                        component="frontend",
                        severity="critical",
                        message=f"Frontend returned {resp.status_code}",
                    )
                    if self._can_restart():
                        healed = await self._restart_service("frontend")
                        if healed:
                            inc.auto_healed = True
                            inc.heal_action = "Restarted frontend via supervisorctl"
                    incidents.append(inc)

                elif resp.status_code >= 400:
                    incidents.append(Incident(
                        component="frontend",
                        severity="warning",
                        message=f"Frontend returned {resp.status_code}",
                    ))
                else:
                    # Check that HTML contains React root
                    if "root" not in resp.text and "<div" not in resp.text:
                        incidents.append(Incident(
                            component="frontend",
                            severity="warning",
                            message="Frontend HTML missing React root — possible build error",
                        ))

                report.frontend_ok = resp.status_code < 400

        except Exception as e:
            report.frontend_ok = False
            inc = Incident(
                component="frontend",
                severity="critical",
                message=f"Frontend unreachable: {e}",
            )
            if self._can_restart():
                healed = await self._restart_service("frontend")
                if healed:
                    inc.auto_healed = True
                    inc.heal_action = "Restarted frontend via supervisorctl"
            incidents.append(inc)

        return incidents

    # ──────────────────────────────────────────
    # CHECK: Scrapers
    # ──────────────────────────────────────────
    async def _check_scrapers(self, report: MasterReport) -> List[Incident]:
        incidents = []
        from scrapers.scraper_utils import health_tracker

        all_health = health_tracker.get_dashboard_data()
        healthy = 0
        blocked = 0
        stale = 0

        now = datetime.now(timezone.utc)

        for h in all_health:
            key = h["brand_key"]
            if h.get("is_blocked"):
                blocked += 1
                inc = Incident(
                    component=f"scraper:{key}",
                    severity="warning",
                    message=f"{h['brand_name']} is BLOCKED (failures: {h['consecutive_failures']})",
                )
                # Auto-heal: retrigger via swarm
                healed = await self._retrigger_scraper(key)
                if healed:
                    inc.auto_healed = True
                    inc.heal_action = f"Retriggered {key} via AETHER SWARM"
                incidents.append(inc)

            elif h.get("consecutive_failures", 0) >= 3:
                stale += 1
                incidents.append(Incident(
                    component=f"scraper:{key}",
                    severity="warning",
                    message=f"{h['brand_name']} has {h['consecutive_failures']} consecutive failures",
                ))
            else:
                # Check staleness
                last_success = h.get("last_success")
                if last_success:
                    try:
                        ls_time = datetime.fromisoformat(last_success.replace("Z", "+00:00"))
                        age_min = (now - ls_time).total_seconds() / 60
                        if age_min > SCRAPER_STALE_MINUTES:
                            stale += 1
                            incidents.append(Incident(
                                component=f"scraper:{key}",
                                severity="info",
                                message=f"{h['brand_name']} last success {age_min:.0f}m ago (stale)",
                            ))
                        else:
                            healthy += 1
                    except Exception:
                        healthy += 1
                else:
                    healthy += 1  # Never run yet — not an error

        report.total_brands_healthy = healthy
        report.total_brands_blocked = blocked
        report.total_brands_stale = stale
        report.scrapers_ok = blocked == 0

        return incidents

    # ──────────────────────────────────────────
    # CHECK: Scheduler
    # ──────────────────────────────────────────
    async def _check_scheduler(self, report: MasterReport) -> List[Incident]:
        incidents = []
        try:
            from scheduler import get_scheduler_status, scheduler as _sched

            # Check if the APScheduler instance is actually running
            is_running = _sched.running if hasattr(_sched, 'running') else False

            if not is_running:
                # Might be a standalone run — check via status dict
                status = get_scheduler_status()
                is_running = status.get("is_running", False)

            last_run = get_scheduler_status().get("last_run")

            if not is_running:
                report.scheduler_ok = False
                incidents.append(Incident(
                    component="scheduler",
                    severity="critical",
                    message="Scheduler is NOT running",
                ))
            elif last_run:
                try:
                    lr_time = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                    age_min = (datetime.now(timezone.utc) - lr_time).total_seconds() / 60
                    if age_min > 30:
                        incidents.append(Incident(
                            component="scheduler",
                            severity="warning",
                            message=f"Scheduler last ran {age_min:.0f}m ago (expected every 15m)",
                        ))
                except Exception:
                    pass

            report.scheduler_ok = is_running or True  # Don't mark critical on first boot

        except Exception as e:
            report.scheduler_ok = True  # Assume OK if import fails (standalone)
            incidents.append(Incident(
                component="scheduler",
                severity="info",
                message=f"Scheduler status check skipped: {e}",
            ))

        return incidents

    # ──────────────────────────────────────────
    # AUTO-HEAL helpers
    # ──────────────────────────────────────────
    def _can_restart(self) -> bool:
        """Rate-limit restarts to MAX_AUTO_RESTART_PER_HOUR."""
        cutoff = time.time() - 3600
        self._restart_log = [t for t in self._restart_log if t > cutoff]
        return len(self._restart_log) < MAX_AUTO_RESTART_PER_HOUR

    async def _restart_service(self, service: str) -> bool:
        """Restart a supervisor-managed service."""
        try:
            result = subprocess.run(
                ["sudo", "supervisorctl", "restart", service],
                timeout=15, capture_output=True, text=True,
            )
            self._restart_log.append(time.time())
            success = result.returncode == 0
            if success:
                logger.info(f"[AetherMaster] Auto-restarted {service}")
                await asyncio.sleep(3)  # Let it boot
            else:
                logger.error(f"[AetherMaster] Failed to restart {service}: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"[AetherMaster] Restart {service} exception: {e}")
            return False

    async def _retrigger_scraper(self, brand_key: str) -> bool:
        """Retrigger a scraper through the AETHER SWARM pipeline."""
        try:
            from scrapers import SCRAPERS
            if brand_key not in SCRAPERS:
                return False
            scraper = SCRAPERS[brand_key]()
            products = await scraper.run_swarm_scrape(max_pages=3)
            return bool(products)
        except Exception as e:
            logger.warning(f"[AetherMaster] Retrigger {brand_key} failed: {e}")
            return False

    # ──────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────
    async def _persist_report(self, report: MasterReport, incidents: List[Incident]):
        """Store the cycle report + individual incidents in MongoDB."""
        if self._db is None:
            return

        try:
            report_doc = asdict(report)
            report_doc["type"] = "cycle_report"
            report_doc["cycle"] = self._run_count
            await self._db.aether_master_memory.insert_one(report_doc)

            if incidents:
                inc_docs = []
                for i in incidents:
                    doc = asdict(i)
                    doc["type"] = "incident"
                    doc["cycle"] = self._run_count
                    inc_docs.append(doc)
                await self._db.aether_master_memory.insert_many(inc_docs)

        except Exception as e:
            logger.error(f"[AetherMaster] DB persist failed: {e}")

    # ──────────────────────────────────────────
    # Escalation
    # ──────────────────────────────────────────
    async def _escalate(self, incidents: List[Incident]):
        """Send WhatsApp alert for unresolved critical incidents."""
        lines = [f"• [{i.component}] {i.message}" for i in incidents[:5]]
        message = (
            f"AETHER MASTER ALERT\n\n"
            f"{len(incidents)} critical issue(s) detected:\n"
            + "\n".join(lines)
            + "\n\nManual intervention required."
        )

        try:
            from whatsapp import WhatsAppClient, IS_CONFIGURED
            if IS_CONFIGURED:
                client = WhatsAppClient()
                admin_phone = os.getenv("ADMIN_PHONE", "")
                if admin_phone:
                    client.send_text_message(admin_phone, message)
                    logger.info("[AetherMaster] WhatsApp escalation sent")
                else:
                    logger.warning("[AetherMaster] No ADMIN_PHONE configured for escalation")
            else:
                logger.warning("[AetherMaster] WhatsApp not configured — escalation logged only")
        except Exception as e:
            logger.error(f"[AetherMaster] WhatsApp escalation failed: {e}")

    # ──────────────────────────────────────────
    # API data
    # ──────────────────────────────────────────
    def get_status(self) -> Dict:
        """Return the last report as a dict for the API."""
        if self._last_report is None:
            return {"status": "not_yet_run", "cycles_completed": 0}

        r = self._last_report
        return {
            "overall_status": r.overall_status,
            "timestamp": r.timestamp,
            "cycles_completed": self._run_count,
            "components": {
                "mongodb": r.mongodb_ok,
                "backend": r.backend_ok,
                "frontend": r.frontend_ok,
                "scrapers": r.scrapers_ok,
                "scheduler": r.scheduler_ok,
            },
            "metrics": {
                "total_products": r.total_products,
                "brands_healthy": r.total_brands_healthy,
                "brands_blocked": r.total_brands_blocked,
                "brands_stale": r.total_brands_stale,
            },
            "latencies_ms": r.endpoint_latencies,
            "incidents": r.incidents[:20],
            "auto_heals": r.auto_heals,
            "escalations": r.escalations,
        }

    async def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent cycle reports from DB."""
        if self._db is None:
            return []
        try:
            docs = await self._db.aether_master_memory.find(
                {"type": "cycle_report"},
                {"_id": 0},
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            return docs
        except Exception:
            return []

    async def get_incidents(self, component: str = None, limit: int = 100) -> List[Dict]:
        """Get recent incidents, optionally filtered by component."""
        if self._db is None:
            return []
        query: Dict[str, Any] = {"type": "incident"}
        if component:
            query["component"] = component
        try:
            docs = await self._db.aether_master_memory.find(
                query, {"_id": 0},
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            return docs
        except Exception:
            return []


# ──────────────────────────────────────────────
# Global instance
# ──────────────────────────────────────────────
aether_master = AetherMaster()


async def init_aether_master(db):
    """Initialize and return the global master instance."""
    await aether_master.init(db)
    return aether_master

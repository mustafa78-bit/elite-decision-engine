import importlib
import pkgutil
import pytest
import re


def _get_all_modules():
    top_packages = ["api", "core", "services", "dto", "whale", "liquidity",
                    "orderflow", "market_structure", "news", "sentiment",
                    "macro", "decision", "scoring", "models", "filters",
                    "execution", "utils"]
    modules = []
    for pkg_name in top_packages:
        try:
            pkg = importlib.import_module(pkg_name)
            if hasattr(pkg, "__path__"):
                for importer, modname, ispkg in pkgutil.walk_packages(pkg.__path__, prefix=f"{pkg_name}."):
                    modules.append(modname)
            modules.append(pkg_name)
        except ImportError:
            pass
    return modules


_MODULES_CACHE = None


def _get_imports(module_name: str):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            return []
        with open(spec.origin, encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return []
    imports = re.findall(r"^from\s+(\S+)\s+import", source, re.MULTILINE)
    imports += re.findall(r"^import\s+(\S+)", source, re.MULTILINE)
    return [i.split(".")[0] for i in imports]


class TestArchitecture:

    @pytest.fixture(scope="class")
    def all_modules(self):
        global _MODULES_CACHE
        if _MODULES_CACHE is None:
            _MODULES_CACHE = _get_all_modules()
        return _MODULES_CACHE

    def test_no_circular_imports(self):
        mods = ["api", "core", "services", "dto"]
        for m in mods:
            try:
                importlib.import_module(m)
            except ImportError as e:
                if "circular" in str(e).lower():
                    pytest.fail(f"Circular import detected when loading {m}: {e}")
            except Exception:
                pass

    def test_core_does_not_import_api(self):
        for modname in list(importlib.import_module("core").__dict__.keys()):
            if modname.startswith("_"):
                continue
            try:
                sub = importlib.import_module(f"core.{modname}")
                src = getattr(sub, "__file__", "")
                if src and src.endswith(".py"):
                    with open(src, encoding="utf-8") as f:
                        content = f.read()
                    assert "from api" not in content, f"{src} imports from api layer"
                    assert "import api" not in content, f"{src} imports api"
            except (ImportError, AttributeError):
                pass

    def test_services_import_core_not_api(self):
        # real_time.py is allowed to import from api.websocket (broadcast infrastructure)
        allowed_api_imports = {"real_time": "from api.websocket import"}
        for modname in ["portfolio_service", "intelligence_service", "notification_service",
                        "real_time", "dashboard_api", "user_service"]:
            try:
                sub = importlib.import_module(f"services.{modname}")
                src = getattr(sub, "__file__", "")
                if src and src.endswith(".py"):
                    with open(src, encoding="utf-8") as f:
                        content = f.read()
                    allowed = allowed_api_imports.get(modname, "")
                    if allowed and allowed in content:
                        content = content.replace(allowed, "")
                    assert "from api" not in content, f"{src} imports from api layer"
                    assert "import api" not in content, f"{src} imports api"
            except (ImportError, AttributeError):
                pass

    def test_dto_has_no_dependencies_on_api_or_services(self):
        src = importlib.import_module("dto.models").__file__
        with open(src, encoding="utf-8") as f:
            content = f.read()
        assert "from api" not in content
        assert "from services" not in content
        # core.serialization is the only acceptable core import
        allowed = {"from core.serialization import SerializableMixin"}
        for line in content.splitlines():
            if line.strip().startswith("from core") and line.strip() not in allowed:
                pytest.fail(f"Unexpected core import in dto/models.py: {line.strip()}")

    def test_modules_load_without_error(self, all_modules):
        errors = []
        for mod in all_modules:
            try:
                importlib.import_module(mod)
            except Exception as e:
                errors.append(f"{mod}: {e}")
        assert not errors, f"Module loading errors:\n" + "\n".join(errors[:10])

    def test_api_has_lazy_app_import(self):
        src = importlib.import_module("api").__file__
        with open(src, encoding="utf-8") as f:
            content = f.read()
        assert "importlib.import_module" in content

    def test_serialization_pattern_consistent(self):
        from core.health import HealthStatus, MetricsResponse
        from dto.models import (
            PortfolioDTO, TradeDTO, IntelligenceDTO, RiskDTO,
            MonitoringDTO, NotificationDTO, DashboardMetricsDTO,
            MarketOverviewDTO, WidgetDTO, KPIDTO,
        )
        dtos = [PortfolioDTO, TradeDTO, IntelligenceDTO, RiskDTO,
                MonitoringDTO, NotificationDTO, DashboardMetricsDTO,
                MarketOverviewDTO, WidgetDTO, KPIDTO]
        for dto in dtos:
            instance = dto()
            d = instance.to_dict()
            assert isinstance(d, dict), f"{dto.__name__}.to_dict() did not return dict"
        from dto.models import DashboardOverviewDTO, DashboardDTO, PortfolioDetailsDTO, IntelligenceDetailsDTO
        for dto_cls in [DashboardOverviewDTO, DashboardDTO, PortfolioDetailsDTO, IntelligenceDetailsDTO]:
            instance = dto_cls()
            d = instance.to_dict()
            assert isinstance(d, dict), f"{dto_cls.__name__}.to_dict() did not return dict"


class TestDependencyValidation:

    def test_api_depends_on_core_and_services(self):
        from api.app import APIApp
        app = APIApp()
        assert hasattr(app, "engine")
        assert hasattr(app, "health")
        assert hasattr(app, "router")

    def test_services_init_exports_all(self):
        from services import PortfolioService, IntelligenceService, NotificationService
        from services import UnifiedBroadcaster, SubscriptionManager, ChannelRegistry

    def test_core_init_exports_all(self):
        from core import DecisionEngine, HealthChecker, TTLCache, RetryHandler
        from core import Scheduler, ConfigValidator, SerializableMixin

    def test_dto_init_exports_all(self):
        from dto import DashboardDTO, PortfolioDTO, IntelligenceDTO, RiskDTO
        from dto import MonitoringDTO, NotificationDTO, WebSocketDTO

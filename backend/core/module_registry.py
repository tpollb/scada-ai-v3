"""Module Registry — loads and manages modules dynamically"""
from pathlib import Path
from typing import Dict, Any, Optional
from structlog import get_logger
import importlib
import yaml

log = get_logger()


class Module:
    """Represents a loaded module"""

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.config: Dict[str, Any] = {}
        self.tools: list = []
        self.prompts: Dict[str, str] = {}
        self._loaded = False

    def load(self):
        """Load module configuration and tools"""
        config_path = self.path / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        # Load prompts
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_")
        }

        # Load tools
        try:
            tools_module = importlib.import_module(f"modules.{self.name}.tools")
            self.tools = getattr(tools_module, "TOOLS", [])
        except ImportError:
            self.tools = []

        self._loaded = True
        log.info(f"Module loaded: {self.name}", tools=len(self.tools))

    @property
    def is_loaded(self) -> bool:
        return self._loaded


class ModuleRegistry:
    """Central registry for all modules"""

    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self._modules: Dict[str, Module] = {}

    def discover_modules(self) -> list[str]:
        """Discover available modules"""
        modules = []
        for path in self.modules_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                modules.append(path.name)
        return sorted(modules)

    def load_module(self, name: str) -> Optional[Module]:
        """Load a single module"""
        if name in self._modules and self._modules[name].is_loaded:
            return self._modules[name]

        module_path = self.modules_dir / name
        if not module_path.exists():
            log.error(f"Module not found: {name}")
            return None

        module = Module(name, module_path)
        try:
            module.load()
            self._modules[name] = module
            return module
        except Exception as e:
            log.error(f"Failed to load module {name}", error=str(e))
            return None

    def load_all(self, enabled: list[str] | None = None) -> Dict[str, Module]:
        """Load all enabled modules"""
        available = self.discover_modules()
        to_load = enabled if enabled else available

        for name in to_load:
            if name in available:
                self.load_module(name)
            else:
                log.warning(f"Module not found: {name}")

        return self._modules

    def get_module(self, name: str) -> Optional[Module]:
        """Get a loaded module"""
        return self._modules.get(name)

    def get_all_tools(self) -> list:
        """Get all tools from all loaded modules"""
        tools = []
        for module in self._modules.values():
            tools.extend(module.tools)
        return tools

    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts from all loaded modules"""
        prompts = {}
        for module in self._modules.values():
            prompts.update(module.prompts)
        return prompts


# Singleton instance
_registry: Optional[ModuleRegistry] = None


def get_registry() -> ModuleRegistry:
    """Get or create the global registry"""
    global _registry
    if _registry is None:
        modules_dir = Path(__file__).parent.parent / "modules"
        _registry = ModuleRegistry(modules_dir)
    return _registry

#!/usr/bin/env python3
"""
Реализует сохранение промптов для всех модулей
"""
from pathlib import Path

print("=" * 80)
print("РЕАЛИЗАЦИЯ СОХРАНЕНИЯ ПРОМПТОВ")
print("=" * 80)

# ============================================================================
# 1. ОБНОВЛЯЕМ update_prompt в config.py
# ============================================================================
print("\n【1】Обновляем endpoint update_prompt в config.py")
print("-" * 80)

config_path = Path("backend/api/routes/config.py")
config_content = config_path.read_text(encoding="utf-8")

old_update = '''@router.put("/modules/{module_name}/prompts/{prompt_name}")
async def update_prompt(module_name: str, prompt_name: str, req: UpdatePromptRequest):
    """Обновляет промпт модуля"""
    log.info("Prompt update requested", module=module_name, prompt=prompt_name)
    return {"status": "ok", "message": "Промпт будет использован в следующих запросах"}'''

new_update = '''@router.put("/modules/{module_name}/prompts/{prompt_name}")
async def update_prompt(module_name: str, prompt_name: str, req: UpdatePromptRequest):
    """
    Обновляет промпт модуля.
    
    Сохраняет изменённый промпт в prompts_override.yaml внутри папки модуля.
    При загрузке модуля override имеет приоритет над prompts.py.
    """
    import yaml
    from pathlib import Path as PathLib
    
    log.info("Prompt update requested", module=module_name, prompt=prompt_name, chars=len(req.prompt_text))
    
    # Путь к override файлу модуля
    module_path = PathLib(__file__).parent.parent.parent / "modules" / module_name
    override_path = module_path / "prompts_override.yaml"
    
    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Модуль {module_name} не найден")
    
    # Читаем существующий override или создаём новый
    overrides = {}
    if override_path.exists():
        try:
            with open(override_path, "r", encoding="utf-8") as f:
                overrides = yaml.safe_load(f) or {}
        except Exception as e:
            log.warning("Failed to read existing override", error=str(e))
    
    # Обновляем промпт
    overrides[prompt_name] = req.prompt_text
    
    # Сохраняем
    try:
        with open(override_path, "w", encoding="utf-8") as f:
            yaml.dump(overrides, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        log.info("Prompt saved to override", module=module_name, prompt=prompt_name, path=str(override_path))
        
        # Перезагружаем модуль чтобы изменения применились
        try:
            from core.module_registry import get_registry
            registry = get_registry()
            if module_name in registry._modules and registry._modules[module_name].is_loaded:
                registry.reload_module(module_name)
                log.info("Module reloaded to apply prompt changes", module=module_name)
        except Exception as reload_error:
            log.warning("Module reload failed (will apply on next restart)", error=str(reload_error))
        
        return {
            "status": "ok", 
            "message": f"Промпт '{prompt_name}' сохранён и применён",
            "saved_to": str(override_path)
        }
    except Exception as e:
        log.error("Failed to save prompt", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {e}")'''

if old_update in config_content:
    config_content = config_content.replace(old_update, new_update)
    config_path.write_text(config_content, encoding="utf-8")
    print("✅ update_prompt теперь сохраняет в prompts_override.yaml")
else:
    print("⚠️  Старый update_prompt не найден")

# ============================================================================
# 2. ОБНОВЛЯЕМ module_registry
# ============================================================================
print("\n【2】Обновляем module_registry для чтения override")
print("-" * 80)

registry_path = Path("backend/core/module_registry.py")
registry_content = registry_path.read_text(encoding="utf-8")

old_load = '''        # Load prompts (только строки, функции игнорируем)
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_") and isinstance(getattr(prompts_module, name), str)
        }'''

new_load = '''        # Load prompts (только строки, функции игнорируем)
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_") and isinstance(getattr(prompts_module, name), str)
        }
        
        # Override prompts from prompts_override.yaml (если есть)
        override_path = self.path / "prompts_override.yaml"
        if override_path.exists():
            try:
                with open(override_path, "r", encoding="utf-8") as f:
                    overrides = yaml.safe_load(f) or {}
                for name, text in overrides.items():
                    if isinstance(text, str) and name in self.prompts:
                        self.prompts[name] = text
                        log.debug(f"Prompt overridden: {self.name}/{name}")
            except Exception as e:
                log.warning(f"Failed to load prompts override for {self.name}", error=str(e))'''

if old_load in registry_content:
    registry_content = registry_content.replace(old_load, new_load)
    registry_path.write_text(registry_content, encoding="utf-8")
    print("✅ module_registry теперь читает prompts_override.yaml")
else:
    print("⚠️  Блок загрузки prompts не найден")

# ============================================================================
# 3. ДОБАВЛЯЕМ reload_module
# ============================================================================
print("\n【3】Добавляем reload_module в module_registry")
print("-" * 80)

if "def reload_module" in registry_content:
    print("✅ reload_module уже существует")
else:
    reload_method = '''
    def reload_module(self, name: str) -> bool:
        """Перезагружает модуль (перечитывает prompts и tools)"""
        if name not in self._modules:
            return False
        
        module = self._modules[name]
        module._loaded = False
        module.prompts = {}
        module.tools = []
        
        # Перезагружаем
        module.load()
        log.info(f"Module reloaded: {name}", prompts=len(module.prompts))
        return True
'''
    
    marker = "    def get_all_prompts"
    if marker in registry_content:
        registry_content = registry_content.replace(marker, reload_method + "\n" + marker)
        registry_path.write_text(registry_content, encoding="utf-8")
        print("✅ Добавлен метод reload_module")
    else:
        print("⚠️  Не удалось добавить reload_module")

# ============================================================================
# 4. ОБНОВЛЯЕМ interpreter.py
# ============================================================================
print("\n【4】Обновляем interpreter.py")
print("-" * 80)

interpreter_path = Path("backend/modules/deep_analysis/llm/interpreter.py")
if interpreter_path.exists():
    interpreter_content = interpreter_path.read_text(encoding="utf-8")
    
    old_import = "from modules.deep_analysis.prompts import DDA_SYSTEM_PROMPT, build_dda_prompt"
    new_import = """from modules.deep_analysis.prompts import DDA_SYSTEM_PROMPT as DEFAULT_DDA_SYSTEM_PROMPT, build_dda_prompt


def _get_dda_system_prompt() -> str:
    \"\"\"Получает system prompt из registry (с учётом override) или fallback на дефолт.\"\"\"
    try:
        from core.module_registry import get_registry
        registry = get_registry()
        if "deep_analysis" in registry._modules:
            module = registry._modules["deep_analysis"]
            if module.is_loaded and "DDA_SYSTEM_PROMPT" in module.prompts:
                return module.prompts["DDA_SYSTEM_PROMPT"]
    except Exception as e:
        log.debug("Failed to get prompt from registry, using default", error=str(e))
    return DEFAULT_DDA_SYSTEM_PROMPT"""
    
    if old_import in interpreter_content:
        interpreter_content = interpreter_content.replace(old_import, new_import)
        interpreter_content = interpreter_content.replace(
            "system_chars=len(DDA_SYSTEM_PROMPT)",
            "system_chars=len(_get_dda_system_prompt())"
        )
        interpreter_content = interpreter_content.replace(
            "DDA_SYSTEM_PROMPT,\n                user_prompt,",
            "_get_dda_system_prompt(),\n                user_prompt,"
        )
        interpreter_content = interpreter_content.replace(
            "DDA_SYSTEM_PROMPT,\n            user_prompt,",
            "_get_dda_system_prompt(),\n            user_prompt,"
        )
        
        interpreter_path.write_text(interpreter_content, encoding="utf-8")
        print("✅ interpreter.py теперь использует registry prompts")
    else:
        print("⚠️  Импорт не найден")
else:
    print("⚠️  interpreter.py не найден")

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)
print()
print("Что реализовано:")
print("1. PUT /config/modules/{name}/prompts/{prompt_name}")
print("   - Сохраняет промпт в modules/{name}/prompts_override.yaml")
print("   - Перезагружает модуль для применения изменений")
print()
print("2. module_registry при загрузке:")
print("   - Читает prompts.py (как раньше)")
print("   - Если есть prompts_override.yaml — применяет override")
print()
print("3. interpreter.py:")
print("   - Берёт DDA_SYSTEM_PROMPT из registry (с override)")
print("   - Fallback на дефолт из prompts.py")
print()
print("СЛЕДУЮЩИЙ ШАГ:")
print("1. Перезапусти backend")
print("2. Протестируй сохранение через API")
print("3. Проверь что изменения применяются")

"""Системный логгер — пишет в файл, читает из файла"""
import re
from datetime import datetime
from typing import Literal
from pathlib import Path
import structlog
import json

LogLevel = Literal["debug", "info", "warning", "error", "critical"]

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

_bridge_installed = False


class SystemLogger:
    def __init__(self):
        self._logger = structlog.get_logger()
        self._in_bridge = False
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._current_file = LOGS_DIR / f"{timestamp}.log"
        self._file_handle = open(self._current_file, "a", encoding="utf-8")
        header = f"# System log started at {datetime.now().isoformat()}\n"
        self._file_handle.write(header)
        self._file_handle.flush()
    
    @property
    def current_file(self):
        return self._current_file
    
    def log(self, level, message, **kwargs):
        timestamp = datetime.now().isoformat(timespec='seconds')
        try:
            data_str = f" | {json.dumps(kwargs, ensure_ascii=False)}" if kwargs else ""
            line = f"[{timestamp}] [{level.upper()}] {message}{data_str}\n"
            self._file_handle.write(line)
            self._file_handle.flush()
        except Exception:
            pass
        if not self._in_bridge:
            log_method = getattr(self._logger, level, self._logger.info)
            log_method(message, **kwargs)
    
    def debug(self, msg, **kw): self.log("debug", msg, **kw)
    def info(self, msg, **kw): self.log("info", msg, **kw)
    def warning(self, msg, **kw): self.log("warning", msg, **kw)
    def error(self, msg, **kw): self.log("error", msg, **kw)
    def critical(self, msg, **kw): self.log("critical", msg, **kw)
    
    def get_logs(self, limit=100, level=None):
        return self.read_file(self._current_file.name, limit=limit, level=level)
    
    def read_file(self, filename, limit=1000, level=None):
        filepath = LOGS_DIR / filename
        try:
            filepath.resolve().relative_to(LOGS_DIR.resolve())
        except ValueError:
            raise ValueError(f"Invalid filename: {filename}")
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filename}")
        entries = []
        seen = set()
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                entry = self._parse_line(line)
                if entry and (level is None or entry["level"] == level):
                    key = (entry["timestamp"], entry["message"])
                    if key not in seen:
                        seen.add(key)
                        entries.append(entry)
        return entries[-limit:]
    
    def _parse_line(self, line):
        match = re.match(r'\[([^\]]+)\]\s+\[([^\]]+)\]\s+(.*)', line)
        if not match:
            return None
        timestamp, level, rest = match.groups()
        if ' | ' in rest:
            msg, data_str = rest.split(' | ', 1)
            try:
                data = json.loads(data_str)
            except Exception:
                data = {"raw": data_str}
        else:
            msg, data = rest, None
        return {"timestamp": timestamp, "level": level.lower(), "message": msg, "data": data}
    
    def list_files(self):
        files = []
        for f in sorted(LOGS_DIR.glob("*.log"), reverse=True):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_current": f == self._current_file
            })
        return files
    
    def clear(self):
        try:
            self._file_handle.seek(0)
            self._file_handle.truncate()
            self._file_handle.write(f"# Log cleared at {datetime.now().isoformat()}\n")
            self._file_handle.flush()
        except Exception:
            pass
    
    def close(self):
        try:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.write(f"# Log closed at {datetime.now().isoformat()}\n")
                self._file_handle.close()
        except Exception:
            pass


system_logger = SystemLogger()


def install_structlog_bridge():
    global _bridge_installed
    if _bridge_installed:
        return
    current = structlog.get_config().get('processors', [])
    for proc in current:
        if getattr(proc, '__name__', '') == 'bridge_processor':
            return
    
    def bridge_processor(logger, method_name, event_dict):
        if event_dict.get('source') == 'core.logger' or system_logger._in_bridge:
            return event_dict
        try:
            system_logger._in_bridge = True
            level_map = {'debug':'debug','info':'info','warning':'warning','warn':'warning','error':'error','critical':'critical','fatal':'critical','exception':'error'}
            level = level_map.get(method_name, 'info')
            event = event_dict.get('event', '')
            data = {k: v for k, v in event_dict.items() if k != 'event'}
            system_logger.log(level, event, **data)
        except Exception:
            pass
        finally:
            system_logger._in_bridge = False
        return event_dict
    
    bridge_processor.__name__ = 'bridge_processor'
    structlog.configure(processors=[bridge_processor, *current])
    _bridge_installed = True
    system_logger.info("Structlog bridge installed", source="core.logger")

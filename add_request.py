#!/usr/bin/env python3
"""
add_request.py - добавляет Request в импорт fastapi
"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Заменяем строку импорта fastapi
old_line = 'from fastapi import APIRouter, HTTPException, Query'
new_line = 'from fastapi import APIRouter, HTTPException, Query, Request'

if old_line in content:
    content = content.replace(old_line, new_line)
    api_path.write_text(content, encoding='utf-8')
    print('✅ Request добавлен в импорт fastapi')
else:
    print('⚠️  Строка импорта не найдена')
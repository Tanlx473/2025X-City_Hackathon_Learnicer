#!/bin/bash
# OCR 模式切换脚本

if [ "$1" == "mathpix" ]; then
    echo "切换到 Mathpix 模式..."
    sed -i '' 's/OCR_MODE=manual/OCR_MODE=mathpix/' .env
    echo "✅ 已切换到 Mathpix 模式"
elif [ "$1" == "manual" ]; then
    echo "切换到 Manual 模式..."
    sed -i '' 's/OCR_MODE=mathpix/OCR_MODE=manual/' .env
    echo "✅ 已切换到 Manual 模式"
else
    echo "用法: ./switch_ocr_mode.sh [mathpix|manual]"
    echo "当前模式: $(grep OCR_MODE .env)"
fi

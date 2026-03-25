"""
generar.py — Helper para el GPT de documentación ISO
El GPT llama a este script pasando el JSON del procedimiento.
Uso interno en el Code Interpreter de ChatGPT.
"""
import json
import sys
import os
import tempfile
import json_a_ficha

def generar_desde_dict(data: dict) -> str:
    """Genera el DOCX y devuelve la ruta del archivo generado."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        tmp_path = f.name

    try:
        out_path = json_a_ficha.generar_ficha(tmp_path)
    finally:
        os.unlink(tmp_path)

    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar.py <archivo.json>")
        sys.exit(1)
    ruta = json_a_ficha.generar_ficha(sys.argv[1])
    print(f"Documento generado: {ruta}")

# Estructura del dict para generar_iso.generar()

```python
data = {
    "codigo": "PC-05", "nombre": "NOMBRE EN MAYÚSCULAS",
    "fecha": "25/03/26", "revision": "00", "paginas": 5,
    "elaborado_por": "Responsable de Calidad y Medio Ambiente",
    "aprobado_por": "Gerencia",
    "historial": [{"rev": "00", "fecha": "25/03/26",
        "descripcion": "Nuevo lanzamiento documental en revisión 00",
        "revisado": "Gerencia",
        "elaborado": "Responsable de Calidad y Medio Ambiente"}],
    "objeto": "...",
    "alcance": "...",
    "definiciones": [{"termino": "término o abreviatura", "definicion": "definición clara"}],  # [] si no aplica
    "responsabilidades": [{"cargo": "Gerencia", "descripcion": "Párrafo narrativo completo sobre el rol de Gerencia.\n\nSegundo párrafo si lo hay."}],
    "entradas": ["Solicitud de...", "Informe de..."],
    "salidas": ["Registro de...", "Notificación a..."],
    "desarrollo": [{"num": "6.1.", "titulo": "Título", "descripcion": "Párrafo 1...\n\nPárrafo 2..."}],
    "archivo": [{"documento": "Nombre del registro",
                 "responsable": "Cargo",
                 "lugar": "Oficinas de GYC / AHORA",
                 "plazo": "3 años / 5 años / Indefinido"}],
    "referencias": {
        "normativas": ["UNE-EN ISO 9001:2015 — Sistemas de gestión de la calidad"],
        "internas":   ["PC-02: «Título del procedimiento relacionado»"]
    },
    "anexos": ["Anexo 1, PC-05: Nombre del anexo"]
}
```

"""
generar_iso.py — Script autocontenido para generar fichas de procedimiento ISO
GÓMEZ Y CRESPO S.A. · ISO 9001/14001
Requiere: python-docx, pc02_template.docx en el mismo directorio

Uso desde Code Interpreter:
    import generar_iso
    ruta = generar_iso.generar(data)   # data es un dict con los campos del procedimiento
"""

import json
import os
import re
import sys
import tempfile

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Busca la plantilla en el mismo directorio que este script
HERE     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "pc02_template.docx")

AZUL  = "95B3D7"
VERDE = "E9EFB1"


# ── Utilidades XML ─────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def set_table_borders(table, sz=4):
    tbl   = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        tblBorders.append(el)
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(tblBorders)


def set_spacing(para, before=0, after=60):
    pPr     = para._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(before))
    spacing.set(qn("w:after"),  str(after))
    old = pPr.find(qn("w:spacing"))
    if old is not None:
        pPr.remove(old)
    pPr.append(spacing)


def set_align(para, align):
    pPr = para._p.get_or_add_pPr()
    jc  = OxmlElement("w:jc")
    align_map = {
        WD_ALIGN_PARAGRAPH.LEFT:    "left",
        WD_ALIGN_PARAGRAPH.CENTER:  "center",
        WD_ALIGN_PARAGRAPH.RIGHT:   "right",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "both",
    }
    jc.set(qn("w:val"), align_map.get(align, "left"))
    old = pPr.find(qn("w:jc"))
    if old is not None:
        pPr.remove(old)
    pPr.append(jc)


def add_run(para, text, size_pt=12, bold=False, italic=False,
            color_hex=None, font="Verdana"):
    run = para.add_run(text)
    run.font.name   = font
    run.font.size   = Pt(size_pt)
    run.font.bold   = bold
    run.font.italic = italic
    if color_hex:
        run.font.color.rgb = RGBColor.from_string(color_hex)
    return run


def add_field(para, field_type, size_pt=10):
    sz_val = str(int(size_pt * 2))

    def make_rPr():
        rPr = OxmlElement("w:rPr")
        sz  = OxmlElement("w:sz")
        sz.set(qn("w:val"), sz_val)
        rPr.append(sz)
        return rPr

    r_begin = OxmlElement("w:r")
    r_begin.append(make_rPr())
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "begin")
    r_begin.append(fc)
    para._p.append(r_begin)

    r_instr = OxmlElement("w:r")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {field_type} "
    r_instr.append(instr)
    para._p.append(r_instr)

    r_end = OxmlElement("w:r")
    r_end.append(make_rPr())
    fc2 = OxmlElement("w:fldChar")
    fc2.set(qn("w:fldCharType"), "end")
    r_end.append(fc2)
    para._p.append(r_end)


def add_section_title(doc, text):
    p = doc.add_paragraph()
    add_run(p, text, size_pt=12, bold=True)
    set_spacing(p, before=120, after=60)
    return p


def blank(doc):
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=40)


# ── Header / Footer ────────────────────────────────────────────────────────────

def _set_wt(wt_node, text):
    wt_node.text = text
    if text != text.strip():
        wt_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def update_header(doc, data):
    hdr = doc.sections[0].header
    if not hdr.tables:
        return
    tbl = hdr.tables[0]

    cell_tit = tbl.cell(0, 1)
    p_tit = cell_tit.paragraphs[0]
    for r in list(p_tit._p.findall(qn("w:r"))):
        p_tit._p.remove(r)
    run = p_tit.add_run(f"{data['codigo']}: {data['nombre']}")
    run.font.name = "Verdana"
    run.font.bold = True
    run.font.size = Pt(14)

    cell_elab = tbl.cell(2, 0)
    wt_nodes = cell_elab._tc.findall(".//" + qn("w:t"))
    if wt_nodes:
        _set_wt(wt_nodes[0], f"Elaborado: {data['elaborado_por']}")

    seen, unique = set(), []
    for c in tbl.rows[2].cells:
        if id(c._tc) not in seen:
            seen.add(id(c._tc))
            unique.append(c)
    cell_apr = unique[-1]
    wt_nodes = cell_apr._tc.findall(".//" + qn("w:t"))
    if wt_nodes:
        _set_wt(wt_nodes[0], f"Revisado y Aprobado: {data['aprobado_por']}")


def update_footer(doc, data):
    ftr = doc.sections[0].footer
    if not ftr.tables:
        return
    tbl = ftr.tables[0]

    wt_nodes = tbl.cell(0, 0)._tc.findall(".//" + qn("w:t"))
    if wt_nodes:
        _set_wt(wt_nodes[0], f"{data['codigo']}: {data['nombre']}")

    wt_nodes = tbl.cell(0, 1)._tc.findall(".//" + qn("w:t"))
    if wt_nodes:
        _set_wt(wt_nodes[0], f"Fecha: {data['fecha']}")
        for wt in wt_nodes[1:]:
            r_elem = wt.getparent()
            if r_elem is not None and r_elem.getparent() is not None:
                r_elem.getparent().remove(r_elem)

    wt_nodes = tbl.cell(1, 0)._tc.findall(".//" + qn("w:t"))
    if wt_nodes:
        _set_wt(wt_nodes[0], f"Rev: {data['revision']}")
        for wt in wt_nodes[1:]:
            r_elem = wt.getparent()
            if r_elem is not None and r_elem.getparent() is not None:
                r_elem.getparent().remove(r_elem)

    cell_11 = tbl.cell(1, 1)
    p_elem  = cell_11.paragraphs[0]._p
    for r in list(p_elem.findall(qn("w:r"))):
        p_elem.remove(r)

    def _make_run(text):
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts")
        fonts.set(qn("w:ascii"), "Verdana")
        fonts.set(qn("w:hAnsi"), "Verdana")
        rPr.append(fonts)
        r.append(rPr)
        t = OxmlElement("w:t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text
        r.append(t)
        return r

    p_elem.append(_make_run("Página "))
    add_field(cell_11.paragraphs[0], "PAGE",     size_pt=10)
    p_elem.append(_make_run(" de "))
    add_field(cell_11.paragraphs[0], "NUMPAGES", size_pt=10)


# ── Secciones del cuerpo ───────────────────────────────────────────────────────

def add_tabla_revisiones(doc, data):
    add_section_title(doc, "CONTROL DE REVISIONES")
    historial   = data["historial"]
    total_filas = len(historial) + 3 + 1
    tbl = doc.add_table(rows=total_filas, cols=5)
    tbl.style = "Table Grid"
    set_table_borders(tbl)
    for i, w in enumerate([Cm(1.332), Cm(1.669), Cm(7.752), Cm(2.588), Cm(2.912)]):
        for cell in tbl.columns[i].cells:
            cell.width = w
    for ri, entry in enumerate(historial):
        for ci, val in enumerate([entry["rev"], entry["fecha"], entry["descripcion"],
                                   entry.get("revisado", ""), entry.get("elaborado", "")]):
            c = tbl.cell(ri, ci)
            set_align(c.paragraphs[0], WD_ALIGN_PARAGRAPH.CENTER if ci < 2 else WD_ALIGN_PARAGRAPH.LEFT)
            add_run(c.paragraphs[0], val, size_pt=11)
    for ci, h in enumerate(["REV", "FECHA", "DESCRIPCIÓN DE LOS CAMBIOS", "REVISADO Y APROBADO", "ELABORADO"]):
        c = tbl.cell(total_filas - 1, ci)
        set_cell_bg(c, AZUL)
        set_align(c.paragraphs[0], WD_ALIGN_PARAGRAPH.CENTER)
        add_run(c.paragraphs[0], h, size_pt=11)
    blank(doc)


def add_tabla_metadatos(doc, data):
    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = "Table Grid"
    set_table_borders(tbl)
    for i, w in enumerate([Cm(5.419), Cm(5.417), Cm(5.417)]):
        tbl.columns[i].cells[0].width = w
    for ci, (label, val, color) in enumerate([
        ("FECHA:", data["fecha"], AZUL),
        ("REVISIÓN:", data["revision"], VERDE),
        ("PÁGINAS:", str(data["paginas"]), AZUL),
    ]):
        c = tbl.cell(0, ci)
        set_cell_bg(c, color)
        set_align(c.paragraphs[0], WD_ALIGN_PARAGRAPH.CENTER)
        add_run(c.paragraphs[0], label + " ", bold=True, size_pt=12)
        add_run(c.paragraphs[0], val, size_pt=12)
    blank(doc)


def add_indice(doc, data):
    add_section_title(doc, "ÍNDICE")
    num = 0
    for sec in ["Objeto.", "Alcance.", "Responsabilidades."]:
        num += 1
        p = doc.add_paragraph()
        add_run(p, f"{num}. {sec}", bold=True, size_pt=10, color_hex=AZUL)
        set_spacing(p, before=40, after=40)
    num += 1
    p = doc.add_paragraph()
    add_run(p, f"{num}. Desarrollo.", bold=True, size_pt=10, color_hex=AZUL)
    set_spacing(p, before=40, after=40)
    for item in data.get("desarrollo", []):
        p_sub = doc.add_paragraph()
        add_run(p_sub, f"    {item['num']} {item['titulo']}.", size_pt=10, color_hex=AZUL)
        set_spacing(p_sub, before=20, after=20)
    for sec in ["Archivo.", "Diagrama de Flujo.", "Referencias.", "Anexos."]:
        num += 1
        p = doc.add_paragraph()
        add_run(p, f"{num}. {sec}", bold=True, size_pt=10, color_hex=AZUL)
        set_spacing(p, before=40, after=40)
    blank(doc)


def add_objeto(doc, data):
    add_section_title(doc, "OBJETO")
    p = doc.add_paragraph()
    add_run(p, data["objeto"], size_pt=12)
    set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
    set_spacing(p, before=60, after=60)
    blank(doc)


def add_alcance(doc, data):
    add_section_title(doc, "ALCANCE")
    p = doc.add_paragraph()
    add_run(p, data["alcance"], size_pt=12)
    set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
    set_spacing(p, before=60, after=60)
    blank(doc)


def add_responsabilidades(doc, data):
    add_section_title(doc, "RESPONSABILIDADES")
    for rol in data.get("responsabilidades", []):
        p = doc.add_paragraph()
        add_run(p, rol["cargo"], bold=True, size_pt=12)
        set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
        set_spacing(p, before=80, after=20)
        for tarea in rol.get("tareas", []):
            p_t = doc.add_paragraph()
            add_run(p_t, f"• {tarea}", size_pt=12)
            set_spacing(p_t, before=0, after=40)
    blank(doc)


def add_desarrollo(doc, data):
    add_section_title(doc, "DESARROLLO")
    for item in data.get("desarrollo", []):
        p = doc.add_paragraph()
        add_run(p, f"{item['num']}  {item['titulo']}", bold=True, size_pt=12)
        set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
        set_spacing(p, before=120, after=60)
        p2 = doc.add_paragraph()
        add_run(p2, item["descripcion"], size_pt=12)
        set_align(p2, WD_ALIGN_PARAGRAPH.JUSTIFY)
        set_spacing(p2, before=0, after=80)
    blank(doc)


def add_archivo(doc, data):
    add_section_title(doc, "ARCHIVO")
    filas = data.get("archivo", [])
    tbl   = doc.add_table(rows=1 + len(filas), cols=3)
    tbl.style = "Table Grid"
    set_table_borders(tbl)
    for i, w in enumerate([Cm(6.75), Cm(4.251), Cm(5.251)]):
        for cell in tbl.columns[i].cells:
            cell.width = w
    for ci, h in enumerate(["Documento", "Responsable", "Lugar"]):
        c = tbl.cell(0, ci)
        set_cell_bg(c, AZUL)
        set_align(c.paragraphs[0], WD_ALIGN_PARAGRAPH.CENTER)
        add_run(c.paragraphs[0], h, bold=True, size_pt=11)
    for ri, fila in enumerate(filas, 1):
        for ci, key in enumerate(["documento", "responsable", "lugar"]):
            c = tbl.cell(ri, ci)
            set_cell_bg(c, VERDE)
            add_run(c.paragraphs[0], fila.get(key, ""), size_pt=11)
    blank(doc)


def add_diagrama(doc):
    add_section_title(doc, "DIAGRAMA DE FLUJO")
    p = doc.add_paragraph()
    add_run(p, "[Insertar diagrama de flujo del procedimiento]",
            italic=True, color_hex="808080", size_pt=12)
    set_spacing(p, before=60, after=60)
    blank(doc)


def add_referencias(doc, data):
    add_section_title(doc, "REFERENCIAS")
    for ref in data.get("referencias", []):
        p = doc.add_paragraph()
        add_run(p, ref, size_pt=12)
        set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
        set_spacing(p, before=0, after=40)
    blank(doc)


def add_anexos(doc, data):
    add_section_title(doc, "ANEXOS")
    anexos = data.get("anexos", [])
    if anexos:
        for anexo in anexos:
            p = doc.add_paragraph()
            add_run(p, anexo, size_pt=12)
            set_align(p, WD_ALIGN_PARAGRAPH.JUSTIFY)
            set_spacing(p, before=0, after=40)
    else:
        p = doc.add_paragraph()
        add_run(p, "No aplica.", italic=True, size_pt=12)


# ── Función principal ──────────────────────────────────────────────────────────

def generar(data: dict, output_dir: str = None) -> str:
    """
    Genera el DOCX del procedimiento ISO a partir de un dict.
    Devuelve la ruta del archivo generado.
    """
    doc  = Document(TEMPLATE)
    body = doc.element.body
    sectPr = body.find(qn("w:sectPr"))
    for child in list(body):
        body.remove(child)
    if sectPr is not None:
        body.append(sectPr)

    section = doc.sections[0]
    section.page_width    = Cm(21)
    section.page_height   = Cm(29.7)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(1.75)
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.43)

    doc.styles["Normal"].font.name = "Verdana"
    doc.styles["Normal"].font.size = Pt(12)

    update_header(doc, data)
    update_footer(doc, data)
    add_tabla_revisiones(doc, data)
    add_tabla_metadatos(doc, data)
    add_indice(doc, data)
    add_objeto(doc, data)
    add_alcance(doc, data)
    add_responsabilidades(doc, data)
    add_desarrollo(doc, data)
    add_archivo(doc, data)
    add_diagrama(doc)
    add_referencias(doc, data)
    add_anexos(doc, data)

    nombre_safe = re.sub(r"[^\w\-]", "_", data.get("nombre", "procedimiento"))[:30]
    filename    = f"{data.get('codigo', 'DOC')}_{nombre_safe}.docx"
    out_dir     = output_dir or HERE
    out_path    = os.path.join(out_dir, filename)
    doc.save(out_path)
    print(f"Documento generado: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_iso.py <archivo.json>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    generar(data)

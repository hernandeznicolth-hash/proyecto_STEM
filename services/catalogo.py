"""
catalogo.py — Carga y gestión de productos desde Excel/CSV de Nicolttissue.
Ruta: base de datos/BASE DE DATOS - NICOLTTISSUE.xlsx (o .csv)
"""

import zipfile
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FOLDER = BASE_DIR / "base de datos"


def _encontrar_archivos() -> tuple[Path | None, Path | None]:
    """Busca archivos .xlsx y .csv en 'base de datos'."""
    DB_FOLDER.mkdir(exist_ok=True)
    xlsx_path = None
    csv_path = None

    for p in DB_FOLDER.iterdir():
        if "NICOLTTISSUE" in p.name.upper():
            if p.suffix.lower() == ".xlsx":
                xlsx_path = p
            elif p.suffix.lower() == ".csv":
                csv_path = p

    if not xlsx_path:
        xlsx_path = DB_FOLDER / "BASE DE DATOS - NICOLTTISSUE.xlsx"
    if not csv_path:
        csv_path = DB_FOLDER / "BASE DE DATOS - NICOLTTISSUE.csv"

    return xlsx_path, csv_path


def _leer_csv(ruta: Path) -> list[dict]:
    """Lee catálogo en formato CSV (delimitado por coma o punto y coma)."""
    productos = []
    if not ruta.is_file():
        return productos

    with open(ruta, "r", encoding="utf-8-sig", errors="replace") as f:
        # Detectar delimitador
        muestra = f.read(2048)
        delimitador = ";" if muestra.count(";") > muestra.count(",") else ","
        f.seek(0)
        reader = csv.reader(f, delimiter=delimitador)

        header_encontrado = False
        for fila in reader:
            if not fila:
                continue
            texto_fila = " ".join(fila).upper()
            if "PRODUCTO" in texto_fila and "PRECIO" in texto_fila:
                header_encontrado = True
                continue
            if header_encontrado and len(fila) >= 3:
                nombre = fila[0].strip()
                ref = fila[1].strip()
                precio_raw = fila[2].strip()
                if not nombre:
                    continue
                try:
                    limpio = precio_raw.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    precio = float(limpio)
                except ValueError:
                    continue
                nombre_completo = f"{nombre} (Ref. {ref})" if ref else nombre
                productos.append({
                    "producto": nombre,
                    "ref": ref,
                    "precio": precio,
                    "nombre_completo": nombre_completo,
                })
    return productos


def _crear_xlsx_desde_items(items: list[dict], ruta_xlsx: Path):
    """Crea un archivo .xlsx válido a partir de una lista de productos."""
    rows = [
        ["BASE DE DATOS -  NICOLTTISSUE", "", ""],
        ["PRODUCTO", "REF", "PRECIO"],
    ]
    for it in items:
        rows.append([it["producto"], it["ref"], it["precio"]])

    strings = []
    str_map = {}

    def get_str_id(s):
        s = str(s)
        if s not in str_map:
            str_map[s] = len(strings)
            strings.append(s)
        return str_map[s]

    sheet_xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    sheet_xml.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
    sheet_xml.append("<sheetData>")

    cols = ["A", "B", "C"]
    for r_idx, row in enumerate(rows, 1):
        sheet_xml.append(f'<row r="{r_idx}">')
        for c_idx, val in enumerate(row):
            col_letter = cols[c_idx]
            cell_ref = f"{col_letter}{r_idx}"
            if isinstance(val, (int, float)):
                sheet_xml.append(f'<c r="{cell_ref}"><v>{val}</v></c>')
            else:
                if val != "":
                    sid = get_str_id(val)
                    sheet_xml.append(f'<c r="{cell_ref}" t="s"><v>{sid}</v></c>')
                else:
                    sheet_xml.append(f'<c r="{cell_ref}"/>')
        sheet_xml.append("</row>")

    sheet_xml.append("</sheetData>")
    sheet_xml.append("</worksheet>")

    sst_xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    sst_xml.append(f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">')
    for s in strings:
        esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        sst_xml.append(f"<si><t>{esc}</t></si>")
    sst_xml.append("</sst>")

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""

    wb_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    try:
        with zipfile.ZipFile(ruta_xlsx, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types)
            z.writestr("_rels/.rels", rels)
            z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
            z.writestr("xl/workbook.xml", wb_xml)
            z.writestr("xl/worksheets/sheet1.xml", "".join(sheet_xml))
            z.writestr("xl/sharedStrings.xml", "".join(sst_xml))
    except Exception:
        pass


def _leer_xlsx(ruta: Path) -> list[dict]:
    """Lee el archivo .xlsx utilizando zipfile + xml."""
    productos = []
    with zipfile.ZipFile(ruta) as z:
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                partes = [r.text for r in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t") if r.text]
                shared_strings.append("".join(partes))

        sheet_tree = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        sheet_data = sheet_tree.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData")
        if sheet_data is None:
            return productos

        header_encontrado = False

        for row in sheet_data.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            celdas = []
            for c in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                t_attr = c.get("t")
                v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                val = v.text if v is not None else ""
                if t_attr == "s" and val != "":
                    try:
                        val = shared_strings[int(val)]
                    except (IndexError, ValueError):
                        pass
                celdas.append(str(val).strip())

            if not celdas or not any(celdas):
                continue

            texto_fila = " ".join(celdas).upper()
            if "PRODUCTO" in texto_fila and "PRECIO" in texto_fila:
                header_encontrado = True
                continue

            if header_encontrado and len(celdas) >= 3:
                nombre_prod = celdas[0]
                ref = celdas[1]
                precio_raw = celdas[2]

                if not nombre_prod:
                    continue

                try:
                    limpio = precio_raw.replace("$", "").replace(" ", "")
                    if "." in limpio and "," in limpio:
                        limpio = limpio.replace(".", "").replace(",", ".")
                    elif "," in limpio:
                        limpio = limpio.replace(",", ".")
                    precio = float(limpio)
                except ValueError:
                    continue

                nombre_completo = f"{nombre_prod} (Ref. {ref})" if ref else nombre_prod
                productos.append({
                    "producto": nombre_prod,
                    "ref": ref,
                    "precio": precio,
                    "nombre_completo": nombre_completo,
                })

    return productos


def cargar_catalogo() -> list[dict]:
    """
    Carga los productos del catálogo buscando en Excel o CSV.
    Si el archivo Excel está dañado o guardado como texto, recurre al CSV y repara el Excel automáticamente.
    """
    xlsx_path, csv_path = _encontrar_archivos()

    # Intentar leer XLSX si existe y es zip válido
    if xlsx_path and xlsx_path.is_file():
        try:
            items = _leer_xlsx(xlsx_path)
            if items:
                return items
        except Exception:
            # Si el XLSX fue corrompido o guardado como texto plano
            pass

    # Intentar leer CSV
    if csv_path and csv_path.is_file():
        items = _leer_csv(csv_path)
        if items:
            # Reparar o crear el XLSX para que coincida
            if xlsx_path:
                _crear_xlsx_desde_items(items, xlsx_path)
            return items

    return []

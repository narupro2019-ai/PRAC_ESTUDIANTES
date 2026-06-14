from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'practicas-secret-2026')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no está configurada en las variables de entorno")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id SERIAL PRIMARY KEY,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            sitio TEXT,
            programa TEXT DEFAULT 'Fisioterapia',
            sede TEXT,
            nivel_practica TEXT,
            grupo TEXT,
            correo TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS docentes (
            id SERIAL PRIMARY KEY,
            documento TEXT UNIQUE,
            nombre TEXT NOT NULL,
            correo TEXT,
            estado TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS escenarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            direccion TEXT,
            cupos INTEGER DEFAULT 10,
            estado TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS asignaciones (
            id SERIAL PRIMARY KEY,
            estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
            docente_id INTEGER REFERENCES docentes(id) ON DELETE SET NULL,
            escenario_id INTEGER REFERENCES escenarios(id) ON DELETE SET NULL,
            nivel_practica TEXT,
            grupo TEXT,
            rotacion INTEGER NOT NULL,
            horario TEXT,
            fecha_inicio DATE,
            fecha_fin DATE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

with app.app_context():
    init_db()

# ==================== DASHBOARD ====================
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.id, e.nombre as estudiante, e.cedula, d.nombre as docente, 
               es.nombre as escenario, a.rotacion, a.horario, a.fecha_inicio, a.fecha_fin
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY a.fecha_creacion DESC LIMIT 10
    ''')
    asignaciones = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', asignaciones=asignaciones)

# ==================== ESTUDIANTES CRUD ====================
@app.route('/estudiantes')
def estudiantes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('estudiantes.html', estudiantes=estudiantes)

@app.route('/register_estudiante', methods=['GET', 'POST'])
def register_estudiante():
    if request.method == 'POST':
        cedula = request.form['cedula'].strip()
        nombre = request.form['nombre'].strip()
        sitio = request.form['sitio'].strip()
        nivel_practica = request.form['nivel_practica']
        programa = request.form.get('programa', 'Fisioterapia')
        sede = request.form['sede'].strip()
        correo = request.form.get('correo', '').strip()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO estudiantes (cedula, nombre, sitio, nivel_practica, programa, sede, correo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (cedula, nombre, sitio, nivel_practica, programa, sede, correo))
            conn.commit()
            flash('✅ Estudiante registrado con éxito', 'success')
            return redirect(url_for('estudiantes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un estudiante con esa cédula', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    return render_template('register_estudiante.html')

@app.route('/edit_estudiante/<int:id>', methods=['GET', 'POST'])
def edit_estudiante(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        cedula = request.form['cedula'].strip()
        nombre = request.form['nombre'].strip()
        sitio = request.form['sitio'].strip()
        nivel_practica = request.form['nivel_practica']
        programa = request.form.get('programa', 'Fisioterapia')
        sede = request.form['sede'].strip()
        correo = request.form.get('correo', '').strip()

        cur.execute('''
            UPDATE estudiantes 
            SET cedula=%s, nombre=%s, sitio=%s, nivel_practica=%s, 
                programa=%s, sede=%s, correo=%s
            WHERE id=%s
        ''', (cedula, nombre, sitio, nivel_practica, programa, sede, correo, id))
        conn.commit()
        flash('✅ Estudiante actualizado', 'success')
        return redirect(url_for('estudiantes'))

    cur.execute("SELECT * FROM estudiantes WHERE id = %s", (id,))
    estudiante = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_estudiante.html', estudiante=estudiante)

@app.route('/delete_estudiante/<int:id>')
def delete_estudiante(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM estudiantes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Estudiante eliminado', 'danger')
    return redirect(url_for('estudiantes'))

# ==================== DOCENTES CRUD ====================
@app.route('/docentes')
def docentes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM docentes ORDER BY nombre")
    docentes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('docentes.html', docentes=docentes)

@app.route('/register_docente', methods=['GET', 'POST'])
def register_docente():
    if request.method == 'POST':
        documento = request.form['documento'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form.get('correo', '').strip()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO docentes (documento, nombre, correo)
                VALUES (%s, %s, %s)
            ''', (documento, nombre, correo))
            conn.commit()
            flash('✅ Docente registrado con éxito', 'success')
            return redirect(url_for('docentes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un docente con ese documento', 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('register_docente.html')

@app.route('/edit_docente/<int:id>', methods=['GET', 'POST'])
def edit_docente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        documento = request.form['documento'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form.get('correo', '').strip()

        cur.execute('''
            UPDATE docentes SET documento=%s, nombre=%s, correo=%s WHERE id=%s
        ''', (documento, nombre, correo, id))
        conn.commit()
        flash('✅ Docente actualizado', 'success')
        return redirect(url_for('docentes'))

    cur.execute("SELECT * FROM docentes WHERE id = %s", (id,))
    docente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_docente.html', docente=docente)

@app.route('/delete_docente/<int:id>')
def delete_docente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM docentes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Docente eliminado', 'danger')
    return redirect(url_for('docentes'))

# ==================== ESCENARIOS CRUD ====================
@app.route('/escenarios')
def escenarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM escenarios ORDER BY nombre")
    escenarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('escenarios.html', escenarios=escenarios)

@app.route('/register_escenario', methods=['GET', 'POST'])
def register_escenario():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        direccion = request.form.get('direccion', '').strip()
        cupos = int(request.form.get('cupos', 10))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO escenarios (nombre, direccion, cupos)
            VALUES (%s, %s, %s)
        ''', (nombre, direccion, cupos))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Escenario registrado', 'success')
        return redirect(url_for('escenarios'))
    return render_template('register_escenario.html')

@app.route('/edit_escenario/<int:id>', methods=['GET', 'POST'])
def edit_escenario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        direccion = request.form.get('direccion', '').strip()
        cupos = int(request.form.get('cupos', 10))

        cur.execute('''
            UPDATE escenarios SET nombre=%s, direccion=%s, cupos=%s WHERE id=%s
        ''', (nombre, direccion, cupos, id))
        conn.commit()
        flash('✅ Escenario actualizado', 'success')
        return redirect(url_for('escenarios'))

    cur.execute("SELECT * FROM escenarios WHERE id = %s", (id,))
    escenario = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_escenario.html', escenario=escenario)

@app.route('/delete_escenario/<int:id>')
def delete_escenario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM escenarios WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Escenario eliminado', 'danger')
    return redirect(url_for('escenarios'))

# ==================== ASIGNACIONES - CRUD COMPLETO ====================

@app.route('/asignaciones')
def asignaciones_list():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT 
            a.id, 
            e.nombre as estudiante, 
            e.cedula,
            d.nombre as docente, 
            es.nombre as escenario, 
            a.rotacion, 
            a.horario, 
            a.fecha_inicio, 
            a.fecha_fin
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY a.fecha_creacion DESC
    ''')
    asignaciones = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('asignaciones.html', asignaciones=asignaciones)


@app.route('/new_assignment', methods=['GET', 'POST'])
def new_assignment():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            estudiante_id = int(request.form['estudiante_id'])
            docente_id = int(request.form['docente_id'])
            escenario_id = int(request.form['escenario_id'])
            rotacion = int(request.form['rotacion'])
            horario = request.form['horario'].strip()
            fecha_inicio = request.form['fecha_inicio']
            fecha_fin = request.form['fecha_fin']

            # Validación de conflictos (incluyendo horario)
            cur.execute('''
                SELECT COUNT(*) AS count FROM asignaciones 
                WHERE estudiante_id = %s 
                  AND horario = %s 
                  AND ((fecha_inicio <= %s AND fecha_fin >= %s) 
                    OR (fecha_inicio <= %s AND fecha_fin >= %s))
            ''', (estudiante_id, horario, fecha_fin, fecha_inicio, fecha_inicio, fecha_fin))
            
            if cur.fetchone()['count'] > 0:
                flash('❌ Conflicto detectado: El estudiante ya tiene asignación en ese horario y fechas', 'danger')
                cur.close()
                conn.close()
                return redirect(url_for('new_assignment'))

            # Inserción en la tabla
            cur.execute('''
                INSERT INTO asignaciones (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin))
            conn.commit()
            flash('✅ Asignación creada correctamente', 'success')
            return redirect(url_for('asignaciones_list'))

        except Exception as e:
            flash(f'Error al guardar: {str(e)}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # GET - cargar listas
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, cedula FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM docentes WHERE estado = 'Activo' ORDER BY nombre")
    docentes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM escenarios WHERE estado = 'Activo' ORDER BY nombre")
    escenarios = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('new_assignment.html', estudiantes=estudiantes, docentes=docentes, escenarios=escenarios)


@app.route('/edit_assignment/<int:id>', methods=['GET', 'POST'])
def edit_assignment(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            estudiante_id = int(request.form['estudiante_id'])
            docente_id = int(request.form['docente_id'])
            escenario_id = int(request.form['escenario_id'])
            rotacion = int(request.form['rotacion'])
            horario = request.form.get('horario', '').strip()
            fecha_inicio = request.form['fecha_inicio']
            fecha_fin = request.form['fecha_fin']

            # Validación de conflictos (incluyendo horario)
            cur.execute('''
                SELECT COUNT(*) AS count FROM asignaciones 
                WHERE estudiante_id = %s 
                  AND horario = %s 
                  AND id <> %s
                  AND ((fecha_inicio <= %s AND fecha_fin >= %s) 
                    OR (fecha_inicio <= %s AND fecha_fin >= %s))
            ''', (estudiante_id, horario, id, fecha_fin, fecha_inicio, fecha_inicio, fecha_fin))
            
            if cur.fetchone()['count'] > 0:
                flash('❌ Conflicto detectado: El estudiante ya tiene asignación en ese horario y fechas', 'danger')
                cur.close()
                conn.close()
                return redirect(url_for('edit_assignment', id=id))

            # Actualización de la asignación
            cur.execute('''
                UPDATE asignaciones 
                SET estudiante_id = %s,
                    docente_id = %s,
                    escenario_id = %s,
                    rotacion = %s,
                    horario = %s,
                    fecha_inicio = %s,
                    fecha_fin = %s
                WHERE id = %s
            ''', (estudiante_id, docente_id, escenario_id, rotacion, 
                  horario, fecha_inicio, fecha_fin, id))
            
            conn.commit()
            flash('✅ Asignación actualizada correctamente', 'success')
            return redirect(url_for('asignaciones_list'))
            
        except Exception as e:
            flash(f'❌ Error al actualizar: {str(e)}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # ==================== GET - Cargar datos para editar ====================
    cur = conn.cursor()
    cur.execute('SELECT * FROM asignaciones WHERE id = %s', (id,))
    asignacion = cur.fetchone()

    if not asignacion:
        flash('Asignación no encontrada', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('asignaciones_list'))

    # Cargar listas para los selects
    cur.execute("SELECT id, nombre, cedula FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    
    cur.execute("SELECT id, nombre FROM docentes WHERE estado = 'Activo' ORDER BY nombre")
    docentes = cur.fetchall()
    
    cur.execute("SELECT id, nombre FROM escenarios WHERE estado = 'Activo' ORDER BY nombre")
    escenarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('edit_assignment.html', 
                         asignacion=asignacion, 
                         estudiantes=estudiantes, 
                         docentes=docentes, 
                         escenarios=escenarios)



@app.route('/delete_assignment/<int:id>')
def delete_assignment(id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar que la asignación existe antes de eliminar
        cur.execute("SELECT id FROM asignaciones WHERE id = %s", (id,))
        if not cur.fetchone():
            flash('Asignación no encontrada', 'warning')
            return redirect(url_for('asignaciones_list'))

        cur.execute("DELETE FROM asignaciones WHERE id = %s", (id,))
        conn.commit()
        
        flash('🗑️ Asignación eliminada correctamente', 'danger')
        return redirect(url_for('asignaciones_list'))
        
    except Exception as e:
        flash(f'❌ Error al eliminar la asignación: {str(e)}', 'danger')
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# ==================== REPORTES ====================
# ==================== EXPORTAR A EXCEL ====================
@app.route('/generate_excel_report')
def generate_excel_report():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            e.nombre AS "Estudiante",
            e.cedula AS "Documento",
            es.nombre AS "Escenario",
            d.nombre AS "Docente",
            a.rotacion AS "Rotación",
            a.horario AS "Horario",
            a.fecha_inicio AS "Fecha Inicio",
            a.fecha_fin AS "Fecha Fin",
            es.direccion AS "Dirección"
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY e.nombre ASC, a.rotacion ASC
    ''')
    
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        flash('⚠️ No hay asignaciones para exportar', 'warning')
        return redirect(url_for('index'))

    import pandas as pd
    import io

    columns = ["Estudiante", "Documento", "Escenario", "Docente", "Rotación", 
               "Horario", "Fecha Inicio", "Fecha Fin", "Dirección"]
    
    df = pd.DataFrame(rows, columns=columns)

    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Programación de Prácticas')
        
        worksheet = writer.sheets['Programación de Prácticas']

        # Ajustar ancho de columnas
        for col in range(1, len(columns) + 1):
            worksheet.column_dimensions[
                worksheet.cell(row=1, column=col).column_letter
            ].width = 20 

        # Formato de fechas (para que no aparezcan ####)
        date_format = 'DD/MM/YYYY'
        for row in range(2, len(rows) + 2):
            worksheet.cell(row=row, column=7).number_format = date_format  # Fecha Inicio
            worksheet.cell(row=row, column=8).number_format = date_format  # Fecha Fin
    
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Programacion_Practicas.xlsx'
    )



@app.route('/generate_pdf_report')
def generate_pdf_report():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import pandas as pd
        import io

        # ✅ MISMA LÓGICA QUE EL EXCEL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT 
                e.nombre AS "Estudiante",
                e.cedula AS "Documento",
                es.nombre AS "Escenario",
                d.nombre AS "Docente",
                a.rotacion AS "Rotación",
                a.horario AS "Horario",
                a.fecha_inicio AS "Fecha Inicio",
                a.fecha_fin AS "Fecha Fin",
                es.direccion AS "Dirección"
            FROM asignaciones a
            JOIN estudiantes e ON a.estudiante_id = e.id
            JOIN docentes d ON a.docente_id = d.id
            JOIN escenarios es ON a.escenario_id = es.id
            ORDER BY e.nombre ASC, a.rotacion ASC
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            flash('⚠️ No hay asignaciones para exportar', 'warning')
            return redirect(url_for('index'))

        # ✅ MISMA LÓGICA QUE EL EXCEL
        columns = ["Estudiante", "Documento", "Escenario", "Docente", "Rotación",
                   "Horario", "Fecha Inicio", "Fecha Fin", "Dirección"]
        df = pd.DataFrame(rows, columns=columns)
        for col in ["Fecha Inicio", "Fecha Fin"]:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime("%d/%m/%Y").fillna("")

        # ── Colores ──
        AZUL_HEADER   = colors.HexColor('#003366')
        AZUL_ROTACION = colors.HexColor('#1F4E79')
        VERDE_DOCENTE = colors.HexColor('#E2EFDA')
        GRIS_ALTERNO  = colors.HexColor('#F2F2F2')
        AZUL_TITULO   = colors.HexColor('#2E75B6')
        BLANCO        = colors.white

        PAGE_W = landscape(letter)[0] - 2*cm
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                leftMargin=1*cm, rightMargin=1*cm,
                                topMargin=1.2*cm, bottomMargin=1.2*cm)
        styles = getSampleStyleSheet()
        elements = []

        # ── Estilos ──
        title_s = ParagraphStyle('t', parent=styles['Title'], fontName='Helvetica-Bold',
                                 fontSize=14, textColor=AZUL_TITULO, alignment=TA_CENTER, spaceAfter=4)
        rot_s   = ParagraphStyle('r', parent=styles['Normal'], fontName='Helvetica-Bold',
                                 fontSize=9, textColor=BLANCO, alignment=TA_LEFT)
        esc_s   = ParagraphStyle('e', parent=styles['Normal'], fontName='Helvetica-Bold',
                                 fontSize=8, textColor=BLANCO, alignment=TA_CENTER)
        doc_s   = ParagraphStyle('d', parent=styles['Normal'], fontName='Helvetica-BoldOblique',
                                 fontSize=7.5, textColor=colors.HexColor('#1F4E79'), alignment=TA_CENTER)
        est_s   = ParagraphStyle('s', parent=styles['Normal'], fontName='Helvetica',
                                 fontSize=7.5, alignment=TA_CENTER)

        elements.append(Paragraph("PROGRAMACIÓN DE PRÁCTICAS ACADÉMICAS 2026-1", title_s))
        elements.append(Spacer(1, 10))

        # ── Agrupar por Horario (grupo AM/PM) y luego por Rotación ──
        for horario, df_horario in df.groupby("Horario", sort=True):

            # Banda de grupo (AM / PM)
            grupo_tbl = Table([[Paragraph(f"Horario: {horario}", rot_s)]], colWidths=[PAGE_W])
            grupo_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), AZUL_TITULO),
                ('TOPPADDING',    (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ]))
            elements.append(grupo_tbl)
            elements.append(Spacer(1, 6))

            for rotacion, df_rot in df_horario.groupby("Rotación", sort=True):
                fecha_ini = df_rot["Fecha Inicio"].iloc[0]
                fecha_fin = df_rot["Fecha Fin"].iloc[0]

                # Escenarios en el orden en que aparecen
                escenarios_orden = list(dict.fromkeys(df_rot["Escenario"].tolist()))

                esc_data = {}
                for esc in escenarios_orden:
                    sub = df_rot[df_rot["Escenario"] == esc]
                    esc_data[esc] = {
                        "docente":     sub["Docente"].iloc[0],
                        "estudiantes": sub["Estudiante"].tolist()
                    }

                n_cols = len(escenarios_orden)
                col_w  = PAGE_W / n_cols

                # Banda de rotación con fechas
                titulo_rot = f"Rotación {rotacion}:   {fecha_ini}  →  {fecha_fin}"
                rot_tbl = Table([[Paragraph(titulo_rot, rot_s)]], colWidths=[PAGE_W])
                rot_tbl.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0), (-1,-1), AZUL_ROTACION),
                    ('TOPPADDING',    (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ]))
                elements.append(rot_tbl)

                # Tabla: escenarios en columnas, estudiantes en filas
                header_row  = [Paragraph(e, esc_s) for e in escenarios_orden]
                docente_row = [Paragraph(esc_data[e]["docente"], doc_s) for e in escenarios_orden]

                max_est = max(len(esc_data[e]["estudiantes"]) for e in escenarios_orden)
                student_rows = []
                for i in range(max_est):
                    student_rows.append([
                        Paragraph(
                            esc_data[e]["estudiantes"][i] if i < len(esc_data[e]["estudiantes"]) else "",
                            est_s
                        )
                        for e in escenarios_orden
                    ])

                data_tbl = [header_row, docente_row] + student_rows
                ts = [
                    ('BACKGROUND', (0,0), (-1,0), AZUL_HEADER),
                    ('TEXTCOLOR',  (0,0), (-1,0), BLANCO),
                    ('BACKGROUND', (0,1), (-1,1), VERDE_DOCENTE),
                    ('GRID',    (0,0), (-1,-1), 0.5, colors.HexColor('#BFBFBF')),
                    ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING',    (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]
                for ri in range(2, len(data_tbl)):
                    ts.append(('BACKGROUND', (0,ri), (-1,ri),
                               GRIS_ALTERNO if ri % 2 == 0 else BLANCO))

                tbl = Table(data_tbl, colWidths=[col_w]*n_cols)
                tbl.setStyle(TableStyle(ts))
                elements.append(tbl)
                elements.append(Spacer(1, 10))

        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True,
                         download_name='Programacion_Practicas_2026-1.pdf')

    except Exception as e:
        flash(f'Error generando PDF: {str(e)}', 'danger')
        return redirect(url_for('index'))



        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

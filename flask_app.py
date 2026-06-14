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

# ==================== ASIGNACIONES ====================
@app.route('/asignaciones')
def asignaciones_list():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.id, e.nombre as estudiante, e.cedula, d.nombre as docente, 
               es.nombre as escenario, a.rotacion, a.horario, 
               a.fecha_inicio, a.fecha_fin
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
        estudiante_id = int(request.form['estudiante_id'])
        docente_id = int(request.form['docente_id'])
        escenario_id = int(request.form['escenario_id'])
        rotacion = int(request.form['rotacion'])
        horario = request.form.get('horario', '')
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        # Validación de conflicto
        cur.execute('''
            SELECT COUNT(*) FROM asignaciones 
            WHERE estudiante_id = %s 
            AND ((fecha_inicio <= %s AND fecha_fin >= %s) OR (fecha_inicio <= %s AND fecha_fin >= %s))
        ''', (estudiante_id, fecha_fin, fecha_inicio, fecha_inicio, fecha_fin))
        
        if cur.fetchone()[0] > 0:
            flash('❌ Conflicto de horario/fechas con otra asignación del estudiante', 'danger')
            conn.close()
            return redirect(url_for('new_assignment'))

        cur.execute('''
            INSERT INTO asignaciones 
            (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin))
        conn.commit()
        flash('✅ Asignación creada correctamente', 'success')
        return redirect(url_for('index'))

    # GET
    cur.execute("SELECT id, nombre, cedula FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM docentes ORDER BY nombre")
    docentes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM escenarios ORDER BY nombre")
    escenarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('new_assignment.html', estudiantes=estudiantes, docentes=docentes, escenarios=escenarios)

# ==================== REPORTES ====================
@app.route('/generate_excel_report')
def generate_excel_report():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT e.nombre as Estudiante, e.cedula as Cedula, e.nivel_practica as Nivel,
               e.grupo, d.nombre as Docente, es.nombre as Escenario, 
               a.rotacion as Rotacion, a.horario, a.fecha_inicio as "Fecha Inicio", 
               a.fecha_fin as "Fecha Fin"
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY e.nivel_practica, a.rotacion, e.nombre
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        flash('No hay asignaciones para exportar', 'warning')
        return redirect(url_for('index'))

    columns = ["Estudiante", "Cédula", "Nivel", "Grupo", "Docente", "Escenario", 
               "Rotación", "Horario", "Fecha Inicio", "Fecha Fin"]
    df = pd.DataFrame(rows, columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Programación')
        ws = writer.sheets['Programación']
        for col in range(1, len(columns) + 1):
            ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 25

    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='Programacion_Practicas_2026-1.xlsx')

@app.route('/generate_pdf_report')
def generate_pdf_report():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT e.nombre, e.cedula, e.nivel_practica, d.nombre as docente, 
                   es.nombre as escenario, a.rotacion, a.horario, a.fecha_inicio, a.fecha_fin
            FROM asignaciones a
            JOIN estudiantes e ON a.estudiante_id = e.id
            JOIN docentes d ON a.docente_id = d.id
            JOIN escenarios es ON a.escenario_id = es.id
            ORDER BY e.nivel_practica, a.rotacion
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("PROGRAMACIÓN DE PRÁCTICAS ACADÉMICAS 2026-1", styles['Title']))
        elements.append(Spacer(1, 20))

        data = [["Estudiante", "Cédula", "Nivel", "Docente", "Escenario", "Rotación", "Horario", "Inicio", "Fin"]]
        for row in rows:
            data.append([str(x) for x in row])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='Programacion_Practicas_2026-1.pdf')

    except Exception as e:
        flash(f'Error generando PDF: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

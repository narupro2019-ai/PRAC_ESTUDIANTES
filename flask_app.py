from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

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
            documento TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            codigo TEXT,
            semestre INTEGER,
            grupo TEXT,
            nivel_practica TEXT,
            direccion TEXT,
            celular TEXT,
            correo TEXT,
            eps TEXT,
            acudiente TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS docentes (
            id SERIAL PRIMARY KEY,
            documento TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            correo TEXT,
            estado TEXT DEFAULT 'Activo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS escenarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            codigo TEXT,
            direccion TEXT,
            cupos INTEGER DEFAULT 10,
            estado TEXT DEFAULT 'Activo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS asignaciones (
            id SERIAL PRIMARY KEY,
            estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
            docente_id INTEGER REFERENCES docentes(id) ON DELETE CASCADE,
            escenario_id INTEGER REFERENCES escenarios(id) ON DELETE CASCADE,
            rotacion INTEGER NOT NULL CHECK (rotacion BETWEEN 1 AND 4),
            horario TEXT NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(estudiante_id, rotacion)
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
        SELECT a.id, e.nombre as estudiante, e.documento, d.nombre as docente, 
               es.nombre as escenario, a.rotacion, a.horario, a.fecha_inicio, a.fecha_fin
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY a.fecha_creacion DESC LIMIT 15
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
        documento = request.form['documento'].strip()
        nombre = request.form['nombre'].strip()
        codigo = request.form.get('codigo', '').strip()
        semestre = int(request.form.get('semestre', 0))
        grupo = request.form.get('grupo', '').strip()
        nivel_practica = request.form.get('nivel_practica', '').strip()
        direccion = request.form.get('direccion', '').strip()
        celular = request.form.get('celular', '').strip()
        correo = request.form.get('correo', '').strip()
        eps = request.form.get('eps', '').strip()
        acudiente = request.form.get('acudiente', '').strip()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO estudiantes (documento, nombre, codigo, semestre, grupo, nivel_practica, direccion, celular, correo, eps, acudiente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (documento, nombre, codigo, semestre, grupo, nivel_practica, direccion, celular, correo, eps, acudiente))
            conn.commit()
            flash('✅ Estudiante registrado con éxito', 'success')
            return redirect(url_for('estudiantes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un estudiante con ese documento', 'danger')
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
        documento = request.form['documento'].strip()
        nombre = request.form['nombre'].strip()
        codigo = request.form.get('codigo', '').strip()
        semestre = int(request.form.get('semestre', 0))
        grupo = request.form.get('grupo', '').strip()
        nivel_practica = request.form.get('nivel_practica', '').strip()
        direccion = request.form.get('direccion', '').strip()
        celular = request.form.get('celular', '').strip()
        correo = request.form.get('correo', '').strip()
        eps = request.form.get('eps', '').strip()
        acudiente = request.form.get('acudiente', '').strip()

        try:
            cur.execute('''
                UPDATE estudiantes SET documento=%s, nombre=%s, codigo=%s, semestre=%s, grupo=%s, 
                nivel_practica=%s, direccion=%s, celular=%s, correo=%s, eps=%s, acudiente=%s
                WHERE id=%s
            ''', (documento, nombre, codigo, semestre, grupo, nivel_practica, direccion, celular, correo, eps, acudiente, id))
            conn.commit()
            flash('✅ Estudiante actualizado', 'success')
            return redirect(url_for('estudiantes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Documento ya existe', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

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
                INSERT INTO docentes (documento, nombre, correo) VALUES (%s, %s, %s)
            ''', (documento, nombre, correo))
            conn.commit()
            flash('✅ Docente registrado', 'success')
            return redirect(url_for('docentes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Documento ya existe', 'danger')
            conn.rollback()
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

        try:
            cur.execute('''
                UPDATE docentes SET documento=%s, nombre=%s, correo=%s WHERE id=%s
            ''', (documento, nombre, correo, id))
            conn.commit()
            flash('✅ Docente actualizado', 'success')
            return redirect(url_for('docentes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Documento ya existe', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

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
        codigo = request.form.get('codigo', '').strip()
        direccion = request.form.get('direccion', '').strip()
        cupos = int(request.form.get('cupos', 10))

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO escenarios (nombre, codigo, direccion, cupos) VALUES (%s, %s, %s, %s)
            ''', (nombre, codigo, direccion, cupos))
            conn.commit()
            flash('✅ Escenario registrado', 'success')
            return redirect(url_for('escenarios'))
        finally:
            cur.close()
            conn.close()
    return render_template('register_escenario.html')

@app.route('/edit_escenario/<int:id>', methods=['GET', 'POST'])
def edit_escenario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        codigo = request.form.get('codigo', '').strip()
        direccion = request.form.get('direccion', '').strip()
        cupos = int(request.form.get('cupos', 10))

        cur.execute('''
            UPDATE escenarios SET nombre=%s, codigo=%s, direccion=%s, cupos=%s WHERE id=%s
        ''', (nombre, codigo, direccion, cupos, id))
        conn.commit()
        flash('✅ Escenario actualizado', 'success')
        cur.close()
        conn.close()
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

# ==================== ASIGNACIONES CRUD CON VALIDACIÓN ====================
@app.route('/asignaciones')
def asignaciones_list():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.id, e.nombre as estudiante, d.nombre as docente, es.nombre as escenario,
               a.rotacion, a.horario, a.fecha_inicio, a.fecha_fin
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
        horario = request.form['horario'].strip()
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        # Validación de conflictos
        cur.execute('''
            SELECT COUNT(*) FROM asignaciones 
            WHERE estudiante_id = %s 
              AND horario = %s 
              AND ((fecha_inicio <= %s AND fecha_fin >= %s) 
                OR (fecha_inicio <= %s AND fecha_fin >= %s))
        ''', (estudiante_id, horario, fecha_fin, fecha_inicio, fecha_inicio, fecha_fin))
        
        if cur.fetchone()['count'] > 0:
            flash('❌ Conflicto detectado: El estudiante ya tiene asignación en ese horario y fechas', 'danger')
            conn.close()
            return redirect(url_for('new_assignment'))

        try:
            cur.execute('''
                INSERT INTO asignaciones (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin))
            conn.commit()
            flash('✅ Asignación creada correctamente', 'success')
            return redirect(url_for('asignaciones_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # GET - cargar listas
    cur.execute("SELECT id, nombre, documento FROM estudiantes ORDER BY nombre")
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
        estudiante_id = int(request.form['estudiante_id'])
        docente_id = int(request.form['docente_id'])
        escenario_id = int(request.form['escenario_id'])
        rotacion = int(request.form['rotacion'])
        horario = request.form['horario'].strip()
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        # Validación de conflictos (excluyendo la asignación actual)
        cur.execute('''
            SELECT COUNT(*) FROM asignaciones 
            WHERE estudiante_id = %s AND id != %s
              AND horario = %s 
              AND ((fecha_inicio <= %s AND fecha_fin >= %s) 
                OR (fecha_inicio <= %s AND fecha_fin >= %s))
        ''', (estudiante_id, id, horario, fecha_fin, fecha_inicio, fecha_inicio, fecha_fin))
        
        if cur.fetchone()['count'] > 0:
            flash('❌ Conflicto detectado', 'danger')
            conn.close()
            return redirect(url_for('edit_assignment', id=id))

        cur.execute('''
            UPDATE asignaciones 
            SET estudiante_id=%s, docente_id=%s, escenario_id=%s, rotacion=%s, 
                horario=%s, fecha_inicio=%s, fecha_fin=%s
            WHERE id=%s
        ''', (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin, id))
        conn.commit()
        flash('✅ Asignación actualizada', 'success')
        cur.close()
        conn.close()
        return redirect(url_for('asignaciones_list'))

    cur.execute("SELECT * FROM asignaciones WHERE id = %s", (id,))
    asignacion = cur.fetchone()
    cur.execute("SELECT id, nombre, documento FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM docentes ORDER BY nombre")
    docentes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM escenarios ORDER BY nombre")
    escenarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('edit_assignment.html', asignacion=asignacion, estudiantes=estudiantes, docentes=docentes, escenarios=escenarios)

@app.route('/delete_assignment/<int:id>')
def delete_assignment(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asignaciones WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Asignación eliminada', 'danger')
    return redirect(url_for('asignaciones_list'))

# ==================== EXPORTAR A EXCEL ====================
@app.route('/export_excel')
def export_excel():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            e.nombre AS estudiante,
            e.documento,
            es.nombre AS escenario,
            d.nombre AS docente,
            a.rotacion,
            a.horario,
            a.fecha_inicio,
            a.fecha_fin,
            es.direccion
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        JOIN docentes d ON a.docente_id = d.id
        JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY e.nombre, a.rotacion
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Programación Prácticas"

    # Headers
    headers = ["Estudiante", "Documento", "Escenario", "Docente", "Rotación", 
               "Horario", "Fecha Inicio", "Fecha Fin", "Dirección"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

    # Datos reales
    for r_idx, row in enumerate(rows, 2):
        for c_idx, value in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=value)

    filename = "Programacion_Practicas.xlsx"
    wb.save(filename)
    
    return send_file(filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

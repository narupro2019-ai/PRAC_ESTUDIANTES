from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'practicas-secret-2026')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no está configurada")
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
            codigo TEXT UNIQUE,
            semestre INTEGER,
            grupo TEXT,
            nivel_practica TEXT,
            direccion TEXT,
            celular TEXT,
            correo TEXT,
            eps TEXT,
            acudiente TEXT,
            contacto_emergencia TEXT,
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
            codigo TEXT UNIQUE,
            direccion TEXT,
            cupos INTEGER DEFAULT 5,
            estado TEXT DEFAULT 'Activo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS asignaciones (
            id SERIAL PRIMARY KEY,
            estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
            docente_id INTEGER REFERENCES docentes(id) ON DELETE SET NULL,
            escenario_id INTEGER REFERENCES escenarios(id) ON DELETE SET NULL,
            rotacion INTEGER NOT NULL,
            horario TEXT,
            fecha_inicio DATE,
            fecha_fin DATE,
            estado TEXT DEFAULT 'Activa',
            fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        SELECT a.id, e.nombre as estudiante, d.nombre as docente, 
               es.nombre as escenario, a.rotacion, a.horario, a.estado
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        LEFT JOIN docentes d ON a.docente_id = d.id
        LEFT JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY a.fecha_asignacion DESC LIMIT 10
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
        semestre = int(request.form.get('semestre', 1))
        grupo = request.form.get('grupo', '').strip()
        nivel_practica = request.form.get('nivel_practica', '').strip()
        direccion = request.form.get('direccion', '').strip()
        celular = request.form.get('celular', '').strip()
        correo = request.form.get('correo', '').strip()
        eps = request.form.get('eps', '').strip()
        acudiente = request.form.get('acudiente', '').strip()
        contacto_emergencia = request.form.get('contacto_emergencia', '').strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO estudiantes (documento, nombre, codigo, semestre, grupo, nivel_practica, 
                                       direccion, celular, correo, eps, acudiente, contacto_emergencia)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (documento, nombre, codigo, semestre, grupo, nivel_practica, direccion, celular, 
                  correo, eps, acudiente, contacto_emergencia))
            conn.commit()
            flash('✅ Estudiante registrado con éxito', 'success')
            return redirect(url_for('estudiantes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un estudiante con ese documento o código', 'danger')
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
        semestre = int(request.form.get('semestre', 1))
        grupo = request.form.get('grupo', '').strip()
        nivel_practica = request.form.get('nivel_practica', '').strip()
        direccion = request.form.get('direccion', '').strip()
        celular = request.form.get('celular', '').strip()
        correo = request.form.get('correo', '').strip()
        eps = request.form.get('eps', '').strip()
        acudiente = request.form.get('acudiente', '').strip()
        contacto_emergencia = request.form.get('contacto_emergencia', '').strip()
        
        try:
            cur.execute('''
                UPDATE estudiantes SET documento=%s, nombre=%s, codigo=%s, semestre=%s, grupo=%s, 
                nivel_practica=%s, direccion=%s, celular=%s, correo=%s, eps=%s, acudiente=%s, 
                contacto_emergencia=%s WHERE id=%s
            ''', (documento, nombre, codigo, semestre, grupo, nivel_practica, direccion, celular, 
                  correo, eps, acudiente, contacto_emergencia, id))
            conn.commit()
            flash('✅ Estudiante actualizado con éxito', 'success')
            return redirect(url_for('estudiantes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Error de duplicado', 'danger')
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
    flash('🗑️ Estudiante eliminado correctamente', 'danger')
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
            flash('✅ Docente actualizado con éxito', 'success')
            return redirect(url_for('docentes'))
        except psycopg2.IntegrityError:
            flash('⚠️ Error de duplicado', 'danger')
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
    flash('🗑️ Docente eliminado correctamente', 'danger')
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
        cupos = int(request.form.get('cupos', 5))
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO escenarios (nombre, codigo, direccion, cupos)
                VALUES (%s, %s, %s, %s)
            ''', (nombre, codigo, direccion, cupos))
            conn.commit()
            flash('✅ Escenario registrado con éxito', 'success')
            return redirect(url_for('escenarios'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un escenario con ese código', 'danger')
            conn.rollback()
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
        cupos = int(request.form.get('cupos', 5))
        
        try:
            cur.execute('''
                UPDATE escenarios SET nombre=%s, codigo=%s, direccion=%s, cupos=%s WHERE id=%s
            ''', (nombre, codigo, direccion, cupos, id))
            conn.commit()
            flash('✅ Escenario actualizado con éxito', 'success')
            return redirect(url_for('escenarios'))
        except psycopg2.IntegrityError:
            flash('⚠️ Error de duplicado', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
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
    flash('🗑️ Escenario eliminado correctamente', 'danger')
    return redirect(url_for('escenarios'))

# ==================== ASIGNACIONES ====================
@app.route('/asignaciones')
def asignaciones():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.*, e.nombre as estudiante, d.nombre as docente, es.nombre as escenario 
        FROM asignaciones a
        JOIN estudiantes e ON a.estudiante_id = e.id
        LEFT JOIN docentes d ON a.docente_id = d.id
        LEFT JOIN escenarios es ON a.escenario_id = es.id
        ORDER BY a.fecha_asignacion DESC
    ''')
    asignaciones_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('asignaciones.html', asignaciones=asignaciones_list)

@app.route('/new_asignacion', methods=['GET', 'POST'])
def new_asignacion():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        estudiante_id = request.form['estudiante_id']
        docente_id = request.form.get('docente_id')
        escenario_id = request.form.get('escenario_id')
        rotacion = int(request.form['rotacion'])
        horario = request.form.get('horario', '')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        cur.execute('''
            INSERT INTO asignaciones (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (estudiante_id, docente_id, escenario_id, rotacion, horario, fecha_inicio, fecha_fin))
        conn.commit()
        flash('✅ Asignación creada con éxito', 'success')
        return redirect(url_for('asignaciones'))

    cur.execute("SELECT id, nombre, documento FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM docentes WHERE estado = 'Activo' ORDER BY nombre")
    docentes = cur.fetchall()
    cur.execute("SELECT id, nombre FROM escenarios WHERE estado = 'Activo' ORDER BY nombre")
    escenarios = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('new_asignacion.html', estudiantes=estudiantes, docentes=docentes, escenarios=escenarios)

if __name__ == '__main__':
    app.run(debug=True)

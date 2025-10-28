# app.py
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, current_app
)
from functools import wraps
import bcrypt
from utils.db import init_db, mysql


app = Flask(__name__)
app.secret_key = 'CHANGE_ME_TO_STRONG_RANDOM_SECRET'   # <<< CHANGE THIS!

# ----------------------------------------------------------------------
# 1. INITIALISE DB + CREATE SCHEMA (runs once per container start)
# ----------------------------------------------------------------------
init_db(app)

with app.app_context():
    cur = mysql.connection.cursor()

    # ----- detectives --------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detectives (
            detective_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ----- cases -------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            status ENUM('Open','Under Investigation','Solved') DEFAULT 'Open',
            detective_id INT,
            FOREIGN KEY (detective_id) REFERENCES detectives(detective_id) ON DELETE SET NULL
        )
    """)

    # ----- clues -------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clues (
            clue_id INT AUTO_INCREMENT PRIMARY KEY,
            case_id INT,
            description TEXT NOT NULL,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
        )
    """)

    # ----- suspects ----------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS suspects (
            suspect_id INT AUTO_INCREMENT PRIMARY KEY,
            case_id INT,
            name VARCHAR(100) NOT NULL,
            evidence_score INT DEFAULT 0,
            remarks VARCHAR(255),
            is_guilty BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
        )
    """)

    # ----- stored procedure --------------------------------------------
    cur.execute("""
        DROP PROCEDURE IF EXISTS update_evidence;
    """)
    cur.execute("""
        CREATE PROCEDURE update_evidence(IN p_suspect_id INT, IN p_value INT)
        BEGIN
            UPDATE suspects
            SET evidence_score = evidence_score + p_value
            WHERE suspect_id = p_suspect_id;
        END
    """)

    # ----- default admin -----------------------------------------------
    cur.execute("SELECT COUNT(*) AS cnt FROM detectives WHERE username='admin'")
    if cur.fetchone()['cnt'] == 0:
        hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO detectives (name, username, password) VALUES (%s,%s,%s)",
            ('Admin Holmes', 'admin', hashed)
        )

    mysql.connection.commit()
    cur.close()


# ----------------------------------------------------------------------
# 2. DECORATORS
# ----------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'detective_id' not in session:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def owns_case(case_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT detective_id FROM cases WHERE case_id=%s", [case_id])
    case = cur.fetchone()
    cur.close()
    if not case:
        return False
    return session.get('is_admin') or case['detective_id'] == session['detective_id']


# ----------------------------------------------------------------------
# 3. AUTH ROUTES
# ----------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM detectives WHERE username=%s", [username])
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['detective_id'] = user['detective_id']
            session['name'] = user['name']
            session['is_admin'] = (username == 'admin')
            return redirect(url_for('dashboard'))

        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip().lower()
        password = request.form['password'].encode('utf-8')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO detectives (name, username, password) VALUES (%s,%s,%s)",
                (name, username, hashed)
            )
            mysql.connection.commit()
            flash('Account created – you can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            if 'Duplicate entry' in str(e):
                flash('Username already taken.', 'danger')
            else:
                flash('Error creating account.', 'danger')
        finally:
            cur.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))


# ----------------------------------------------------------------------
# 4. DASHBOARD
# ----------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    q = request.args.get('q', '').strip()
    cur = mysql.connection.cursor()

    if q:
        cur.execute("""
            SELECT c.*, d.name AS detective_name
            FROM cases c
            LEFT JOIN detectives d ON c.detective_id = d.detective_id
            WHERE c.title LIKE %s
            ORDER BY c.case_id DESC
        """, [f'%{q}%'])
    else:
        cur.execute("""
            SELECT c.*, d.name AS detective_name
            FROM cases c
            LEFT JOIN detectives d ON c.detective_id = d.detective_id
            ORDER BY c.case_id DESC
        """)
    cases = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', cases=cases)


# ----------------------------------------------------------------------
# 5. CASE CRUD
# ----------------------------------------------------------------------
@app.route('/case/add', methods=['GET', 'POST'])
@login_required
def add_case():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form.get('description', '').strip()
        detective_id = request.form.get('detective_id') or session['detective_id']

        cur.execute("""
            INSERT INTO cases (title, description, detective_id, status)
            VALUES (%s, %s, %s, 'Open')
        """, (title, description, detective_id))
        mysql.connection.commit()
        cur.close()
        flash('Case created!', 'success')
        return redirect(url_for('dashboard'))

    cur.execute("SELECT detective_id, name, username FROM detectives ORDER BY name")
    detectives = cur.fetchall()
    cur.close()
    return render_template('add_case.html', detectives=detectives)


@app.route('/case/<int:case_id>')
@login_required
def case_detail(case_id):
    if not owns_case(case_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, d.name AS detective_name
        FROM cases c
        LEFT JOIN detectives d ON c.detective_id = d.detective_id
        WHERE c.case_id = %s
    """, [case_id])
    case = cur.fetchone()

    cur.execute("SELECT * FROM clues WHERE case_id=%s ORDER BY date_added DESC", [case_id])
    clues = cur.fetchall()

    cur.execute("SELECT * FROM suspects WHERE case_id=%s ORDER BY evidence_score DESC", [case_id])
    suspects = cur.fetchall()
    cur.close()
    return render_template('case_detail.html', case=case, clues=clues, suspects=suspects)


@app.route('/case/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_case(case_id):
    if not owns_case(case_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form.get('description', '').strip()
        detective_id = request.form.get('detective_id') or session['detective_id']

        cur.execute("""
            UPDATE cases
            SET title=%s, description=%s, detective_id=%s
            WHERE case_id=%s
        """, (title, description, detective_id, case_id))
        mysql.connection.commit()
        cur.close()
        flash('Case updated.', 'success')
        return redirect(url_for('case_detail', case_id=case_id))

    cur.execute("SELECT * FROM cases WHERE case_id=%s", [case_id])
    case = cur.fetchone()
    cur.execute("SELECT detective_id, name FROM detectives ORDER BY name")
    detectives = cur.fetchall()
    cur.close()
    return render_template('edit_case.html', case=case, detectives=detectives)


# ----------------------------------------------------------------------
# 6. CLUE CRUD
# ----------------------------------------------------------------------
@app.route('/case/<int:case_id>/clue/add', methods=['GET', 'POST'])
@login_required
def add_clue(case_id):
    if not owns_case(case_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    if request.method == 'POST':
        description = request.form['description'].strip()
        impact = int(request.form.get('impact', 0))
        suspect_id = request.form.get('suspect_id')

        cur.execute("INSERT INTO clues (case_id, description) VALUES (%s,%s)", (case_id, description))
        if suspect_id and impact > 0:
            cur.callproc('update_evidence', [int(suspect_id), impact])
        mysql.connection.commit()
        cur.close()
        flash('Clue added.', 'success')
        return redirect(url_for('case_detail', case_id=case_id))

    cur.execute("SELECT title FROM cases WHERE case_id=%s", [case_id])
    title = cur.fetchone()['title']
    cur.execute("SELECT suspect_id, name, evidence_score FROM suspects WHERE case_id=%s", [case_id])
    suspects = cur.fetchall()
    cur.close()
    return render_template('add_clue.html',
                           case={'case_id': case_id, 'title': title},
                           suspects=suspects)


@app.route('/clue/<int:clue_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_clue(clue_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, s.case_id
        FROM clues c
        JOIN cases s ON c.case_id = s.case_id
        WHERE clue_id=%s
    """, [clue_id])
    clue = cur.fetchone()
    if not clue or not owns_case(clue['case_id']):
        cur.close()
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        cur.execute("UPDATE clues SET description=%s WHERE clue_id=%s",
                    (request.form['description'].strip(), clue_id))
        mysql.connection.commit()
        cur.close()
        flash('Clue updated.', 'success')
        return redirect(url_for('case_detail', case_id=clue['case_id']))

    cur.close()
    return render_template('edit_clue.html', clue=clue)


# ----------------------------------------------------------------------
# 7. SUSPECT CRUD
# ----------------------------------------------------------------------
@app.route('/case/<int:case_id>/suspect/add', methods=['GET', 'POST'])
@login_required
def add_suspect(case_id):
    if not owns_case(case_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name'].strip()
        evidence_score = int(request.form.get('evidence_score', 0))
        remarks = request.form.get('remarks', '').strip()

        cur.execute("""
            INSERT INTO suspects (case_id, name, evidence_score, remarks)
            VALUES (%s, %s, %s, %s)
        """, (case_id, name, evidence_score, remarks))
        mysql.connection.commit()
        cur.close()
        flash('Suspect added.', 'success')
        return redirect(url_for('case_detail', case_id=case_id))

    cur.execute("SELECT title FROM cases WHERE case_id=%s", [case_id])
    title = cur.fetchone()['title']
    cur.close()
    return render_template('add_suspect.html',
                           case={'case_id': case_id, 'title': title})


@app.route('/suspect/<int:suspect_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_suspect(suspect_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.*, c.case_id
        FROM suspects s
        JOIN cases c ON s.case_id = c.case_id
        WHERE suspect_id=%s
    """, [suspect_id])
    suspect = cur.fetchone()
    if not suspect or not owns_case(suspect['case_id']):
        cur.close()
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        evidence_score = int(request.form.get('evidence_score', 0))
        remarks = request.form.get('remarks', '').strip()

        cur.execute("""
            UPDATE suspects
            SET name=%s, evidence_score=%s, remarks=%s
            WHERE suspect_id=%s
        """, (name, evidence_score, remarks, suspect_id))
        mysql.connection.commit()
        cur.close()
        flash('Suspect updated.', 'success')
        return redirect(url_for('case_detail', case_id=suspect['case_id']))

    cur.close()
    return render_template('edit_suspect.html', suspect=suspect)


# ----------------------------------------------------------------------
# 8. SOLVE CASE
# ----------------------------------------------------------------------
@app.route('/case/<int:case_id>/solve', methods=['POST'])
@login_required
def solve_case(case_id):
    if not owns_case(case_id):
        return jsonify({'success': False})

    guilty_id = request.form['guilty_suspect']
    cur = mysql.connection.cursor()

    cur.execute("UPDATE cases SET status='Solved' WHERE case_id=%s", [case_id])
    cur.execute("UPDATE suspects SET is_guilty=TRUE WHERE suspect_id=%s", [guilty_id])
    mysql.connection.commit()

    cur.execute("""
        SELECT COUNT(*) AS solved
        FROM cases
        WHERE status='Solved' AND detective_id=%s
    """, [session['detective_id']])
    solved = cur.fetchone()['solved']
    cur.close()

    return jsonify({'success': True, 'easter_egg': solved >= 3})


# ----------------------------------------------------------------------
# 9. DELETE ENDPOINTS (AJAX)
# ----------------------------------------------------------------------
@app.route('/case/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_case(case_id):
    if not owns_case(case_id):
        return jsonify({'success': False})
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cases WHERE case_id=%s", [case_id])
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True})


@app.route('/clue/<int:clue_id>/delete', methods=['POST'])
@login_required
def delete_clue(clue_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT case_id FROM clues WHERE clue_id=%s", [clue_id])
    clue = cur.fetchone()
    if clue and owns_case(clue['case_id']):
        cur.execute("DELETE FROM clues WHERE clue_id=%s", [clue_id])
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    return jsonify({'success': False})


@app.route('/suspect/<int:suspect_id>/delete', methods=['POST'])
@login_required
def delete_suspect(suspect_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT case_id FROM suspects WHERE suspect_id=%s", [suspect_id])
    suspect = cur.fetchone()
    if suspect and owns_case(suspect['case_id']):
        cur.execute("DELETE FROM suspects WHERE suspect_id=%s", [suspect_id])
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    return jsonify({'success': False})


# ----------------------------------------------------------------------
# 10. REPORTS
# ----------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.name, COUNT(c.case_id) AS total_cases
        FROM detectives d
        LEFT JOIN cases c ON d.detective_id = c.detective_id
        GROUP BY d.detective_id
    """)
    cases_per_detective = cur.fetchall()

    cur.execute("SELECT status, COUNT(*) AS count FROM cases GROUP BY status")
    status_stats = cur.fetchall()

    cur.execute("SELECT AVG(evidence_score) AS avg_score FROM suspects WHERE evidence_score>0")
    avg = cur.fetchone()['avg_score'] or 0
    cur.close()

    return render_template('reports.html',
                           cases_per_detective=cases_per_detective,
                           status_stats=status_stats,
                           avg_score=round(avg, 2))


# ----------------------------------------------------------------------
# 11. RUN
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
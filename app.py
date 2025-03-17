from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create uploads directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# In-memory storage for users, tasks, and sticky notes
users = {}
tasks = {}
sticky_notes = {}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists.', 'error')
        else:
            users[username] = {'password': generate_password_hash(password)}
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        if 'task_name' in request.form:
            task_name = request.form['task_name']
            due_date = request.form['due_date']
            priority = request.form['priority']
            category = request.form['category']
            file = request.files.get('file')

            if username not in tasks:
                tasks[username] = []

            task = {
                'name': task_name,
                'due_date': due_date,
                'priority': priority,
                'category': category,
                'completed': False,
                'file': file.filename if file else None
            }
            tasks[username].append(task)

            # Save the file if it exists
            if file:
                file.save(os.path.join('uploads', file.filename))

            return redirect(url_for('dashboard'))

    user_tasks = tasks.get(username, [])
    user_sticky_notes = sticky_notes.get(username, [])
    return render_template('dashboard.html', tasks=user_tasks, sticky_notes=user_sticky_notes)

@app.route('/task/toggle/<task_name>', methods=['POST'])
def toggle_task(task_name):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['username']
    user_tasks = tasks.get(username, [])
    
    for task in user_tasks:
        if task['name'] == task_name:
            task['completed'] = not task['completed']
            return jsonify({'success': True, 'completed': task['completed']})
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/task/delete/<task_name>', methods=['POST'])
def delete_task(task_name):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['username']
    user_tasks = tasks.get(username, [])
    
    tasks[username] = [task for task in user_tasks if task['name'] != task_name]
    return jsonify({'success': True})

@app.route('/sticky_note/add', methods=['POST'])
def add_sticky_note():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    
    if username not in sticky_notes:
        sticky_notes[username] = []
    
    note = {
        'id': data.get('id'),
        'content': data.get('content', ''),
        'color': data.get('color', 'yellow')
    }
    
    sticky_notes[username].append(note)
    return jsonify({'success': True, 'note': note})

@app.route('/sticky_note/update', methods=['POST'])
def update_sticky_note():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    note_id = data.get('id')
    
    if username in sticky_notes:
        for note in sticky_notes[username]:
            if note['id'] == note_id:
                note['content'] = data.get('content', note['content'])
                note['color'] = data.get('color', note['color'])
                return jsonify({'success': True, 'note': note})
    
    return jsonify({'error': 'Note not found'}), 404

@app.route('/sticky_note/delete', methods=['POST'])
def delete_sticky_note():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    note_id = data.get('id')
    
    if username in sticky_notes:
        sticky_notes[username] = [note for note in sticky_notes[username] if note['id'] != note_id]
        return jsonify({'success': True})
    
    return jsonify({'error': 'Note not found'}), 404

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/uploads/<filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Ensure the file exists and is in the uploads directory
    file_path = os.path.join('uploads', filename)
    if not os.path.exists(file_path):
        flash('File not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Send the file as an attachment
    return send_from_directory('uploads', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
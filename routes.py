from flask import Blueprint, render_template, request, redirect, url_for, jsonify, g, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import User, Incident, Action, Playbook, TaskNotification
from app import db
import csv
from io import StringIO
from sqlalchemy import inspect

main_bp = Blueprint('main', __name__)

@main_bp.route('/get_tables', methods=['GET'])
@login_required
def get_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return jsonify({'tables': tables})

# Add this new route to get the full URL
@main_bp.route('/get_tables_url', methods=['GET'])
@login_required
def get_tables_url():
    return jsonify({'url': url_for('main.get_tables', _external=True)})

@main_bp.before_request
def before_request():
    g.active_incidents = Incident.query.filter_by(status='in-progress').all()
    g.closed_incidents = Incident.query.filter_by(status='closed').all()
    g.playbooks = db.session.query(Playbook.name).distinct().all()

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html', active_incidents=g.active_incidents, closed_incidents=g.closed_incidents)

@main_bp.route('/create_incident', methods=['POST'])
def create_incident():
    try:
        title = request.form['title']
        severity = request.form['severity']
        description = request.form['description']
        handler = request.form['handler']
        playbook_id = request.form.get('playbook_id')
        
        if not all([title, severity, description, handler]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        new_incident = Incident(title=title, severity=severity, description=description, handler=handler)
        db.session.add(new_incident)
        db.session.commit()
        
        if playbook_id:
            playbook = Playbook.query.get(playbook_id)
            if playbook:
                for playbook_action in playbook.actions:
                    new_action = Action(
                        incident_id=new_incident.id,
                        title=playbook_action.title,
                        description=playbook_action.description,
                        phase=playbook_action.phase
                    )
                    db.session.add(new_action)
                db.session.commit()
        
        return jsonify({'success': True, 'incident_id': new_incident.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error creating incident: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while creating the incident'}), 500

@main_bp.route('/incident/<int:id>')
def active_incident(id):
    incident = Incident.query.get_or_404(id)
    actions = Action.query.filter_by(incident_id=id).all()
    users = User.query.all()
    return render_template('active_incident.html', incident=incident, actions=actions, users=users)

@main_bp.route('/closed_incident/<int:id>')
def closed_incident(id):
    incident = Incident.query.get_or_404(id)
    actions = Action.query.filter_by(incident_id=id).all()
    return render_template('active_incident.html', incident=incident, actions=actions)

@main_bp.route('/create_action', methods=['POST'])
def create_action():
    try:
        incident_id = request.form['incident_id']
        title = request.form['title']
        description = request.form['description']
        phase = request.form['phase']
        
        new_action = Action(incident_id=incident_id, title=title, description=description, phase=phase)
        db.session.add(new_action)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Action created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@main_bp.route('/update_incident', methods=['POST'])
def update_incident():
    data = request.json
    incident = Incident.query.get_or_404(data['id'])
    
    incident.title = data['title']
    incident.severity = data['severity']
    incident.description = data['description']
    incident.handler = data['handler']
    incident.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/update_incident_status', methods=['POST'])
def update_incident_status():
    data = request.json
    incident = Incident.query.get_or_404(data['id'])
    
    incident.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/assign_action', methods=['POST'])
def assign_action():
    action_id = request.form['action_id']
    assigned_to = request.form['assigned_to']
    
    action = Action.query.get_or_404(action_id)
    action.assigned_to = assigned_to
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/delete_incident/<int:id>', methods=['POST'])
def delete_incident(id):
    incident = Incident.query.get_or_404(id)
    db.session.delete(incident)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/delete_action/<int:id>', methods=['POST'])
def delete_action(id):
    action = Action.query.get_or_404(id)
    db.session.delete(action)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.dashboard'))

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('main.signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main_bp.route('/playbooks')
def playbooks():
    playbooks = Playbook.query.all()
    return render_template('playbooks.html', playbooks=playbooks)

@main_bp.route('/create_playbook', methods=['POST'])
@login_required
def create_playbook():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400

        playbook_name = data.get('playbook_name')
        playbook_description = data.get('playbook_description')
        playbook_created_by = data.get('playbook_created_by')
        playbook_actions = data.get('playbook_actions', [])

        if not playbook_name or not playbook_description or not playbook_created_by:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        new_playbook = Playbook(
            name=playbook_name,
            description=playbook_description,
            created_by=playbook_created_by
        )
        db.session.add(new_playbook)
        db.session.flush()  # This assigns an ID to new_playbook

        for action in playbook_actions:
            new_action = Action(
                playbook_id=new_playbook.id,
                phase=action['phase'],
                title=action['title'],
                description=action['description'],
                is_playbook=True,
                playbook_name=playbook_name
            )
            db.session.add(new_action)

        db.session.commit()

        response_data = {
            'success': True, 
            'message': f'Playbook "{playbook_name}" created successfully',
            'playbook': {
                'id': new_playbook.id,
                'name': new_playbook.name,
                'description': new_playbook.description,
                'created_by': new_playbook.created_by
            }
        }
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        error_message = f"Error creating playbook: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({'success': False, 'error': error_message}), 500

@main_bp.route('/playbook/<int:playbook_id>')
def view_playbook(playbook_id):
    playbook = Playbook.query.get_or_404(playbook_id)
    playbook_actions = playbook.actions
    return render_template('view_playbook.html', playbook=playbook, 
                           playbook_actions=playbook_actions)

@main_bp.route('/add_playbook_action', methods=['POST'])
@login_required
def add_playbook_action():
    data = request.json
    print("Received data:", data)  # Debug print
    try:
        if not all(key in data for key in ['playbook_id', 'phase', 'title', 'description']):
            missing_fields = [key for key in ['playbook_id', 'phase', 'title', 'description'] if key not in data]
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        print("All required fields present")  # Debug print
        
        new_action = Action(
            playbook_id=data['playbook_id'],
            phase=data['phase'],
            title=data['title'],
            description=data['description'],
            is_playbook=True
        )
        print("New action created:", new_action)  # Debug print
        
        db.session.add(new_action)
        print("New action added to session")  # Debug print
        
        db.session.commit()
        print("Session committed")  # Debug print
        
        print("Action added successfully:", new_action)  # Debug print
        return jsonify({'success': True, 'message': 'Action added successfully', 'action_id': new_action.id})
    except Exception as e:
        db.session.rollback()
        error_message = f"Error adding action: {str(e)}"
        print(error_message)  # Debug print
        return jsonify({'success': False, 'error': error_message}), 400

@main_bp.route('/import_playbook', methods=['POST'])
def import_playbook():
    if 'csv_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if file and file.filename.endswith('.csv'):
        playbook_name = request.form['playbook_name']
        playbook_description = request.form['playbook_description']
        playbook_created_by = request.form['playbook_created_by']
        csv_content = file.read().decode('utf-8')
        csv_file = StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)
        
        try:
            new_playbook = Playbook(name=playbook_name, description=playbook_description, created_by=playbook_created_by)
            db.session.add(new_playbook)
            db.session.flush()  # This assigns an ID to new_playbook
            
            for row in csv_reader:
                action = Action(
                    playbook_id=new_playbook.id,
                    title=row.get('Title', '').strip(),
                    description=row.get('Description', '').strip(),
                    phase=row.get('Phase', '').strip(),
                    is_playbook=True,
                    playbook_name=playbook_name
                )
                db.session.add(action)
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Playbook "{playbook_name}" imported successfully'})
        except Exception as e:
            db.session.rollback()
            error_message = f"Error importing playbook: {str(e)}"
            print(error_message)  # Log the error
            return jsonify({'success': False, 'error': error_message})
    
    return jsonify({'success': False, 'error': 'Invalid file format'})


@main_bp.route('/delete_playbook', methods=['POST'])
@login_required
def delete_playbook():
    playbook_name = request.json.get('playbook_name')
    try:
        Action.query.filter_by(is_playbook=True, playbook_name=playbook_name).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': f'Playbook "{playbook_name}" deleted successfully'})
    except Exception as e:
        db.session.rollback()
        error_message = f"Error deleting playbook: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({'success': False, 'error': error_message})

@main_bp.route('/delete_playbook_action', methods=['POST'])
@login_required
def delete_playbook_action():
    action_id = request.json.get('action_id')
    try:
        action = Action.query.get(action_id)
        if action and action.is_playbook:
            db.session.delete(action)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Action deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Action not found or not a playbook action'})
    except Exception as e:
        db.session.rollback()
        error_message = f"Error deleting action: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({'success': False, 'error': error_message})

@main_bp.route('/update_playbook', methods=['POST'])
@login_required
def update_playbook():
    data = request.json
    playbook_name = data.get('name')
    playbook_description = data.get('description')
    actions = data.get('actions', [])

    try:
        # Update playbook actions
        existing_actions = Action.query.filter_by(is_playbook=True, playbook_name=playbook_name).all()
        
        # Delete actions that are no longer present
        for existing_action in existing_actions:
            if not any(action['title'] == existing_action.title for action in actions):
                db.session.delete(existing_action)

        # Update or create actions
        for action in actions:
            existing_action = next((a for a in existing_actions if a.title == action['title']), None)
            if existing_action:
                existing_action.phase = action['phase']
                existing_action.description = action['description']
            else:
                new_action = Action(
                    incident_id=None,
                    title=action['title'],
                    description=action['description'],
                    phase=action['phase'],
                    assigned_to=current_user.username,
                    is_playbook=True,
                    playbook_name=playbook_name
                )
                db.session.add(new_action)

        # Update playbook description (assuming it's stored in the first action)
        first_action = Action.query.filter_by(is_playbook=True, playbook_name=playbook_name).first()
        if first_action:
            first_action.description = playbook_description

        db.session.commit()
        return jsonify({'success': True, 'message': f'Playbook "{playbook_name}" updated successfully'})
    except Exception as e:
        db.session.rollback()
        error_message = f"Error updating playbook: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({'success': False, 'error': error_message})

@main_bp.route('/api/send_task', methods=['POST'])
@login_required
def send_task():
    data = request.json
    action_id = data.get('action_id')
    assigned_user_id = data.get('assigned_user_id')
    
    action = Action.query.get_or_404(action_id)
    assigned_user = User.query.get_or_404(assigned_user_id)
    
    action.assigned_to = assigned_user.username
    notification = TaskNotification(user_id=assigned_user.id, action_id=action.id, incident_id=action.incident_id)
    db.session.add(notification)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task sent successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error sending task: {str(e)}")  # Log the error
        return jsonify({'success': False, 'error': 'Error sending task. Please try again.'})

@main_bp.route('/check_user_exists/<int:user_id>', methods=['GET'])
@login_required
def check_user_exists(user_id):
    user = User.query.get(user_id)
    return jsonify({'exists': user is not None})

@main_bp.route('/assigned_tasks')
@login_required
def assigned_tasks():
    tasks = TaskNotification.query.filter_by(user_id=current_user.id, is_read=False).order_by(TaskNotification.created_at.desc()).all()
    return render_template('assigned_tasks.html', tasks=tasks)

@main_bp.route('/update_task_status', methods=['POST'])
@login_required
def update_task_status():
    task_id = request.json.get('task_id')
    new_status = request.json.get('status')
    task = TaskNotification.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    task.action.status = new_status
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    task_id = request.json.get('task_id')
    task = TaskNotification.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/get_task_count')
@login_required
def get_task_count():
    count = TaskNotification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

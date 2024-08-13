import csv
import sys
from app import create_app, db
from models import Action

def import_playbook(filename, playbook_name):
    app = create_app()
    with app.app_context():
        with open(filename, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                if len(row) != 3:
                    print(f"Skipping invalid row: {row}")
                    continue
                phase, title, description = row
                action = Action(
                    incident_id=None,  # This will be set when the action is assigned to an incident
                    title=title,
                    description=description,
                    phase=phase,
                    assigned_to='Not assigned',  # Default value
                    is_playbook=True,
                    playbook_name=playbook_name
                )
                db.session.add(action)
        db.session.commit()
    print(f"Playbook '{playbook_name}' imported successfully.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python import_playbook.py <csv_filename> <playbook_name>")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    playbook_name = " ".join(sys.argv[2:])
    import_playbook(csv_filename, playbook_name)

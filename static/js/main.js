document.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM fully loaded and parsed');

    const createIncidentForm = document.querySelector('#createIncidentModal form');
    const createPlaybookForm = document.querySelector('#createPlaybookForm');
    const submitCreatePlaybookButton = document.getElementById('submitCreatePlaybook');

    // Apply resizable columns to all tables with 'resizable' class
    const resizableTables = document.querySelectorAll('table.resizable');
    resizableTables.forEach(table => {
        const cols = table.querySelectorAll('th');
        cols.forEach((col) => {
            const resizer = document.createElement('div');
            resizer.classList.add('resizer');
            col.appendChild(resizer);
            createResizableColumn(col, resizer);
        });
    });

    if (createIncidentForm) {
        createIncidentForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(createIncidentForm);
            fetch('/create_incident', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Incident created successfully!');
                    window.location.reload();
                } else {
                    alert('Failed to create incident. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while creating the incident.');
            });
        });
    }

    if (submitCreatePlaybookButton) {
        submitCreatePlaybookButton.addEventListener('click', function() {
            const formData = new FormData(createPlaybookForm);
            const playbookData = {
                playbook_name: formData.get('playbook_name'),
                playbook_description: formData.get('playbook_description'),
                playbook_created_by: formData.get('playbook_created_by')
            };

            console.log('Sending playbook data:', playbookData);  // Log the data being sent

            fetch('/create_playbook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(playbookData),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Parsed response data:', data);
                if (data.success) {
                    alert(data.message);
                    const modal = bootstrap.Modal.getInstance(document.getElementById('createPlaybookModal'));
                    modal.hide();
                    location.reload();
                } else {
                    throw new Error(data.error || 'Unknown error occurred');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('An error occurred while creating the playbook: ' + error.message);
            });
        });
    }

    // Handle status change
    const statusSelects = document.querySelectorAll('.status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const incidentId = this.dataset.incidentId;
            const newStatus = this.value;
            updateIncidentStatus(incidentId, newStatus);
        });
    });
});

function createResizableColumn(col, resizer) {
    let startX, startWidth;

    const mouseDownHandler = function(e) {
        startX = e.clientX;
        startWidth = parseInt(document.defaultView.getComputedStyle(col).width, 10);
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
        resizer.classList.add('resizing');
    };

    const mouseMoveHandler = function(e) {
        const dx = e.clientX - startX;
        col.style.width = `${startWidth + dx}px`;
    };

    const mouseUpHandler = function() {
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
        resizer.classList.remove('resizing');
    };

    resizer.addEventListener('mousedown', mouseDownHandler);
}

function updateIncidentStatus(incidentId, newStatus) {
    fetch('/update_incident_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: incidentId, status: newStatus }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Failed to update incident status. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the incident status.');
    });
}

function deleteIncident(incidentId) {
    if (confirm('Are you sure you want to delete this incident?')) {
        fetch(`/delete_incident/${incidentId}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Incident deleted successfully!');
                window.location.reload();
            } else {
                alert('Failed to delete incident. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the incident.');
        });
    }
}

function deleteAction(actionId) {
    if (confirm('Are you sure you want to delete this action?')) {
        fetch(`/delete_action/${actionId}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Action deleted successfully!');
                window.location.reload();
            } else {
                alert('Failed to delete action. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the action.');
        });
    }
}

function updateTaskCount() {
    fetch('/get_task_count')
        .then(response => response.json())
        .then(data => {
            const taskCountElement = document.getElementById('task-count');
            if (taskCountElement) {
                taskCountElement.textContent = data.count > 0 ? data.count : '';
            }
        });
}

function sendTaskWithAssignment(actionId) {
    const assignedUser = document.querySelector(`#assigned-user-${actionId}`).value;
    if (!assignedUser) {
        alert('Please select a user to assign the task.');
        return;
    }

    fetch('/send_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action_id: actionId, assigned_user: assignedUser }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Task sent successfully!');
            updateTaskCount();
        } else {
            alert('Failed to send task. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while sending the task.');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    updateTaskCount();

    document.querySelectorAll('.send-task').forEach(button => {
        button.addEventListener('click', function() {
            const actionId = this.getAttribute('data-action-id');
            sendTaskWithAssignment(actionId);
        });
    });
});

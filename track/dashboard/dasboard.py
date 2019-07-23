# env FLASK_APP='track.dashboard:dashboard_app' flask run

from flask import Flask
from track.persistence import get_protocol
from track.structure import Project


protocol = 'file:/home/setepenre/work/track/tests/unit/client_orion.json'

backend = get_protocol(protocol)
app = Flask(__name__)


def render_project(page, project: Project):
    page.append('<li>')
    page.append(f'<span>{project.name}<span>')
    page.append(f'<span>{project.description}<span>')

    page.append('<ul>')
    for t in project.trials:

        page.append('<li>')
        page.append(t.uid)
        page.append('</li>')

    page.append('</ul>')
    page.append('</li>')


@app.route('/')
def project():
    projects = backend.fetch_projects()
    page = []

    for project in projects:
        render_project(page, project)

    return ' '.join(page)



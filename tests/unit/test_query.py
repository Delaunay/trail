import os
from track.persistence.local import load_database


def test_local_query():
    if True:
        return
    
    db = load_database(f'{os.path.dirname(__file__)}/../e2e/test.json')

    project_id = db.project_names['ConvnetTest']
    project_obj = db.objects['ConvnetTest']

    for trial in project_obj.trials:
        print(trial.uid)


if __name__ == '__main__':
    test_local_query()

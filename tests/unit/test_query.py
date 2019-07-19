from track.persistence.local import execute_query
from track.structure import Trial, Status, CustomStatus


def test_local_query():
    if True:
        return

    # db = load_database(f'{os.path.dirname(__file__)}/../e2e/test.json')

    # project_id = db.project_names['ConvnetTest']
    # project_obj = db.objects['ConvnetTest']
    #
    # for trial in project_obj.trials:
    #     print(trial.uid)


def check_query(data, query):
    selected = []

    for obj in data:
        if execute_query(obj, query):
            selected.append(obj)

    return selected


def test_execute_query_in():
    data = [
        Trial(name=str(i)) for i in range(0, 20)
    ]

    query = dict(
        name={
            '$in': ['0', '10', '19', '30']
        }
    )

    assert len(check_query(data, query)) == 3


def test_execute_query_status():
    data = [
        Trial(name=str(i)) for i in range(0, 20)
    ]

    query = dict(
        status={
            '$in': [Status.CreatedGroup]
        }
    )

    arr = check_query(data, query)
    assert len(arr) == 20


def test_execute_query_custom_status():
    data = [
        Trial(name=str(i), status=CustomStatus('new', 1)) for i in range(0, 20)
    ] + [
        Trial(name=str(i), status=CustomStatus('interrupted', 1)) for i in range(0, 20)
    ]

    query = dict(
        status={
            '$in': ['new', 'interrupted']
        }
    )

    arr = check_query(data, query)
    assert len(arr) == 40


if __name__ == '__main__':
    test_execute_query_custom_status()



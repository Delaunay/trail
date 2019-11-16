from tests.config import is_travis,  multi_client_launch, remove
from tests.e2e.end_to_end import end_to_end_train
import pytest

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_mongodb_2clients(count=2):
    multi_client_launch('mongodb://localhost:41033', count)


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_pickled_2clients(count=2):
    remove('file.pkl')
    multi_client_launch('pickled://file.pkl', count)
    remove('file.pkl')


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_ephemeral_2clients(count=2):
    multi_client_launch('ephemeral:', count)


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_mongodb(count=2):
    end_to_end_train('mongodb://localhost:41033')


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_pickled(count=2):
    remove('file.pkl')
    end_to_end_train('pickled://file.pkl')
    remove('file.pkl')


@pytest.mark.skipif(is_travis(), reason='Travis is too slow')
def test_e2e_ephemeral(count=2):
    end_to_end_train('ephemeral:')


if __name__ == '__main__':
    # test_e2e_mongodb_2clients()
    # test_e2e_pickled_2clients()
    # test_e2e_ephemeral_2clients()

    remove('file.pkl')
    remove('file.pkl')

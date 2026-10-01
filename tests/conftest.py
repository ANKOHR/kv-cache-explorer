import pytest
from kv_cache_explorer.fixtures import generate


@pytest.fixture
def fixture_dir(tmp_path):
    directory = tmp_path / "inputs"
    generate(directory)
    return directory

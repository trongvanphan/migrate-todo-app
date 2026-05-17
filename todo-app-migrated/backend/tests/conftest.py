import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp.name}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    # Reload modules so settings + engine pick up env
    import importlib
    from app import config as config_module
    importlib.reload(config_module)
    from app import database as db_module
    importlib.reload(db_module)
    from app import models as models_module
    importlib.reload(models_module)
    from app import security as sec_module
    importlib.reload(sec_module)
    from app import auth as auth_module
    importlib.reload(auth_module)
    from app import tasks as tasks_module
    importlib.reload(tasks_module)
    from app import main as main_module
    importlib.reload(main_module)

    db_module.Base.metadata.create_all(bind=db_module.engine)
    with TestClient(main_module.app) as c:
        yield c

    os.unlink(tmp.name)

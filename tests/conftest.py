import os


# Application imports construct the SQLAlchemy engine, but unit tests do not
# connect to a database. Use an obviously non-production URL for test setup.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://rxcheck_test:rxcheck_test@localhost:5432/rxcheck_test",
)

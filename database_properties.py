def get_config():
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': '123'
    }
    return config


def get_db_uri():
    return 'postgresql://postgres:123@localhost:5432/postgres'


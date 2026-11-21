from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def database(url: str) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_engine(
        url, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 3}
    )
    return engine, sessionmaker(engine, expire_on_commit=False)

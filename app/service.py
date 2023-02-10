from app import app, db

from app.models import *

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

class Service():
    def create_db():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)

        with Session(engine) as session:
            spongebob = User(
                name="spongebob",
                fullname="Spongebob Squarepants",
                addresses=[Address(email_address="spongebob@sqlalchemy.org")],
            )
            sandy = User(
                name="sandy",
                fullname="Sandy Cheeks",
                addresses=[
                    Address(email_address="sandy@sqlalchemy.org"),
                    Address(email_address="sandy@squirrelpower.org"),
                ],
            )
            patrick = User(name="patrick", fullname="Patrick Star")
            session.add_all([spongebob, sandy, patrick])
            session.commit()

            session = Session(engine)

            stmt = select(User).where(User.name.in_(["spongebob", "sandy"]))

            for user in session.scalars(stmt):
                print(user)
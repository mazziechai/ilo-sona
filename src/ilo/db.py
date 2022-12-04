import logging
from binascii import crc32
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, session, sessionmaker

LOG = logging.getLogger()
Base = declarative_base()


def sentence_id(sentence: str) -> int:
    return crc32(sentence.encode())  # fine for small strings


class Server(Base):  # bit of room to grow
    __tablename__ = "server"
    id = Column(Integer, primary_key=True)
    challenge_ch_id = Column(Integer)
    approval_ch_id = Column(Integer)
    challenger_role_id = Column(Integer)
    approver_role_id = Column(Integer)
    challenge_number = Column(Integer, default=0)

    def __repr__(self):
        return f"Server({self.id}, {self.challenge_ch_id}, {self.approval_ch_id}, {self.challenger_role_id}, {self.approver_role_id}, {self.challenge_number})"


class Sentence(Base):
    __tablename__ = "sentence"
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    approval_msg_id = Column(Integer, nullable=False, unique=True)
    submitted = Column(DateTime, server_default=func.now(), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    sentence = Column(String(200), nullable=False)

    def __repr__(self):
        return f"Sentence({self.id}, {self.user_id}, {self.submitted}, {self.approved}, {self.used}, '{self.sentence}')"


class ChallengeDB:
    s: session.Session  # use directly if needed

    def __init__(self, database_file: str):
        engine = create_engine(f"sqlite:///{database_file}")  # , echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.s = Session()

    def configure_server(
        self,
        server_id: int,
        challenge_ch_id: Optional[int],
        approval_ch_id: Optional[int],
        challenger_role_id: Optional[int],
        approver_role_id: Optional[int],
        challenge_number: Optional[int],
    ):
        server = self.s.query(Server).get(server_id)
        if not server:
            server = Server(
                id=server_id,
                challenge_ch_id=challenge_ch_id,
                approval_ch_id=approval_ch_id,
                challenger_role_id=challenger_role_id,
                approver_role_id=approver_role_id,
                challenge_number=challenge_number,
            )
            self.s.add(server)
        else:  # typing
            if challenge_ch_id:
                server.challenge_ch_id = challenge_ch_id
            if approval_ch_id:
                server.approval_ch_id = approval_ch_id
            if challenger_role_id:
                server.challenger_role_id = challenger_role_id
            if approver_role_id:
                server.approver_role_id = approver_role_id
            if challenge_number:
                server.challenge_number = challenge_number
        self.s.commit()
        return server

    def get_sentence_by_id(self, id: int) -> Optional[Sentence]:
        return self.s.query(Sentence).get(id)

    def add_sentence(
        self, server_id: int, user_id: int, approval_msg_id: int, sentence: str
    ) -> Sentence:
        sentence = Sentence(
            id=sentence_id(sentence),
            server_id=server_id,
            user_id=user_id,
            approval_msg_id=approval_msg_id,
            sentence=sentence,
        )
        self.s.add(sentence)
        self.s.commit()
        return sentence

    def set_sentence_approval(
        self,
        approval_msg_id: int,
        approval: bool,
    ) -> Optional[Sentence]:
        sentence = (
            self.s.query(Sentence).filter_by(approval_msg_id=approval_msg_id).first()
        )
        sentence.approved = approval  # type: ignore
        # sqlalchemy lies
        self.s.commit()
        return sentence

    def get_use_challenge(self, server_id: int) -> Sentence:
        """Gives"""
        server = self.s.query(Server).filter_by(id=server_id).first()
        if not server:
            server = self.configure_server(server_id, None, None, None, None, 0)
            # TODO
        sentence = (
            self.s.query(Sentence)
            .filter_by(server_id=server_id, approved=True, used=False)
            .order_by(Sentence.submitted)  # oldest
            .first()
        )
        assert sentence
        sentence.used = True  # type: ignore
        server.challenge_number = server.challenge_number + 1  # type: ignore
        # race condition if you +=
        self.s.commit()
        sentence.challenge_number = server.challenge_number
        return sentence  # challenge_number is riding, not committed

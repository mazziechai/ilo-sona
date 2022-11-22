from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    LongField,
    ReferenceField,
    StringField,
)


class Sentences(Document):
    user = LongField()
    submitted = DateTimeField(default=datetime.utcnow)

    sentence = StringField(max_length=200, unique=True)

    verification_message = LongField(required=False)
    verified = BooleanField(default=False)
    used = BooleanField(default=False)


class Challenges(Document):
    number = LongField()
    date = DateTimeField(default=datetime.utcnow)

    sentence = ReferenceField(Sentences)

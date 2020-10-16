from datetime import datetime as dt
from CTFd.models import db, Challenges


class WriteUpChallenges(Challenges):
    id = db.Column(None, db.ForeignKey('challenges.id'), primary_key=True)
    solve_req = db.Column(db.Boolean, default=True, nullable=False)
    for_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    wu_for = db.relationship("Challenges", foreign_keys=[for_id], backref=db.backref('writeup_challenge', uselist=False))

    __mapper_args__ = {
        'polymorphic_identity': 'writeup',
        'inherit_condition': (id == Challenges.id)
    }

    def __init__(self, *args, **kwargs):
        super(WriteUpChallenges, self).__init__(state='hidden', *args, **kwargs)

from lib.firehose_orm import Message #, metadata
# Message is already bound to a MetaData() object in firehose_orm

from app import session

class Message_app(object):
    def __init__(self):
        self.message = session.query(Message).first()
    
    def __repr__(self):
        return self.message.__repr__()

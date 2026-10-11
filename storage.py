"""Local event snapshots or atomic MongoDB documents. No credentials in snapshots."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from copy import deepcopy

class EventStore:
    def __init__(self, uri='', database='crewsync', directory=None):
        self.uri = uri.strip()
        self.directory = Path(directory or Path(__file__).with_name('.data'))
        self.database = database
    def _collection(self):
        from pymongo import MongoClient
        if not self.uri.startswith(('mongodb://','mongodb+srv://')):
            raise ValueError('Use a MongoDB connection URI in MONGODB_URI.')
        client=MongoClient(self.uri,serverSelectionTimeoutMS=5000,connectTimeoutMS=5000,socketTimeoutMS=8000)
        return client, client[self.database]['events']
    def save(self, plan):
        safe_fields=['id','event','date','location','volunteers','shifts','assignments','tasks','announcement']
        document={k:deepcopy(plan[k]) for k in safe_fields if k in plan}
        if not document.get('id'):
            raise ValueError('An event needs an ID before saving.')
        document['updated_at']=datetime.now(timezone.utc).isoformat()
        if self.uri:
            client, collection=self._collection()
            try:
                collection.replace_one({'_id':document['id']},{'_id':document['id'],**document},upsert=True)
            finally:
                client.close()
        else:
            self.directory.mkdir(parents=True,exist_ok=True)
            # Validate IDs before constructing a file path.
            from uuid import UUID
            UUID(document['id'])
            destination=self.directory/(document['id']+'.json')
            temporary=self.directory/(str(uuid4())+'.tmp')
            try:
                temporary.write_text(json.dumps(document,indent=2),encoding='utf-8')
                os.replace(temporary,destination)
            finally:
                temporary.unlink(missing_ok=True)
    def list(self):
        if self.uri:
            client,collection=self._collection()
            try:
                result=list(collection.find({}, {'_id':0}).sort('date',1).limit(100))
            finally:
                client.close()
        else:
            result=[json.loads(p.read_text(encoding='utf-8')) for p in self.directory.glob('*.json')]
        return sorted(result,key=lambda p:(p['date'],p['event']))


class SessionEventStore:
    """Hosted demo records stay inside one visitor's Streamlit session."""
    def __init__(self, records):
        self.records=records
    def save(self, plan):
        fields=['id','event','date','location','volunteers','shifts','assignments','tasks','announcement']
        self.records[plan['id']]={k:deepcopy(plan[k]) for k in fields if k in plan}
    def list(self):
        return sorted(deepcopy(list(self.records.values())),key=lambda p:(p['date'],p['event']))

import tempfile
import unittest
from datetime import date
from copy import deepcopy
from product import *
from storage import EventStore
from coordinator import VOLUNTEERS,SHIFTS,parse_csv

class ProductTests(unittest.TestCase):
    def setUp(self):
        self.v=parse_csv(VOLUNTEERS,'volunteers')
        self.s=parse_csv(SHIFTS,'shifts')
        self.p=new_plan('Demo','2026-10-11','HUB · America/New_York',self.v,self.s)
    def test_proposal_validation_and_unknown_owner(self):
        raw=demo_proposal(date(2026,10,11))
        self.assertEqual(len(validate_proposal(raw,self.v)['shifts']),3)
        raw['tasks'][0]['owner_id']='invented'
        with self.assertRaisesRegex(ValueError,'unknown volunteer'):validate_proposal(raw,self.v)
    def test_malformed_AI_plan_cannot_apply(self):
        for edit in [dict(date='tomorrow'),dict(timezone='not-a-zone'),dict(shifts=[])]:
            raw=demo_proposal(date(2026,10,11));raw.update(edit)
            with self.assertRaises(ValueError):validate_proposal(raw,self.v)
    def test_cancellation_is_proposal_not_mutation(self):
        self.p['tasks']=[dict(id='t1',title='Setup',owner_id='v1',deadline='2026-10-11',done=False)]
        before=deepcopy(self.p)
        result=cancellation_proposal(self.p,'v1')
        self.assertEqual(self.p,before)
        self.assertNotIn('v1',[v['id'] for v in result['volunteers']])
        self.assertEqual(result['tasks'][0]['owner_id'],'')
        self.assertFalse(any('double-booked' in x for x in validate(result['volunteers'],result['shifts'],result['assignments'])))
    def test_task_owner_survives_roster_reordering(self):
        self.p['tasks']=[dict(id='t1',title='Setup',owner_id='v1',deadline='2026-10-11',done=False)]
        reordered=deepcopy(self.v)
        reordered[0]['id']='v9'
        result=new_plan('Demo','2026-10-11','HUB',reordered,self.s,self.p)
        self.assertEqual(result['tasks'][0]['owner_id'],'v9')
    def test_storage_roundtrip_and_update(self):
        with tempfile.TemporaryDirectory() as d:
            store=EventStore(directory=d)
            self.p['secret']='must not persist'
            store.save(self.p)
            loaded=store.list()[0]
            self.assertNotIn('secret',loaded)
            self.assertEqual(loaded['assignments'],self.p['assignments'])
            self.p['event']='Edited'
            store.save(self.p)
            self.assertEqual(len(store.list()),1)
            self.assertEqual(store.list()[0]['event'],'Edited')
    def test_storage_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            store=EventStore(directory=d)
            self.p['id']='../outside'
            with self.assertRaises(ValueError):store.save(self.p)

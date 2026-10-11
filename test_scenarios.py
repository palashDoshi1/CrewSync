"""Chicago football / Mumbai hackathon regression scenarios: synthetic data only."""
import tempfile
import unittest
from copy import deepcopy
from coordinator import parse_csv,schedule,validate,template_messages,display_rows
from product import new_plan,cancellation_proposal,validate_proposal
from storage import EventStore

NAMES=['Alex','Blair','Casey','Drew','Ellis','Finley','Gray','Harper','Jamie','Kai','Logan','Morgan']

def roster():
    rows=['id,name,available_start,available_end,max_shifts']
    windows=[('10:00','12:00'),('12:00','14:00'),('14:00','16:00')]
    for i,name in enumerate(NAMES):
        a,b=windows[i//4];rows.append(f'v{i+1},{name},{a},{b},1')
    return parse_csv('\n'.join(rows),'volunteers')

def event(city):
    titles=['Welcome and check-in','Guest assistance','Cleanup'] if city=='Chicago' else ['Registration desk','Participant support','Demo-room preparation']
    times=[('10:00','12:00'),('12:00','14:00'),('14:00','16:00')]
    ss=parse_csv('id,label,start,end,required\n'+'\n'.join(f's{i+1},{label},{a},{b},3' for i,(label,(a,b)) in enumerate(zip(titles,times))),'shifts')
    return new_plan('Chicago football' if city=='Chicago' else 'Mumbai university hackathon', '2026-10-16' if city=='Chicago' else '2026-10-17', 'Stadium entrance · America/Chicago' if city=='Chicago' else 'Main auditorium · Asia/Kolkata',roster(),ss)

class EventScenarios(unittest.TestCase):
    def test_both_events_have_nine_valid_assignments(self):
        for city in ['Chicago','Mumbai']:
            with self.subTest(city=city):
                p=event(city)
                self.assertEqual(len(p['assignments']),9)
                self.assertEqual(validate(p['volunteers'],p['shifts'],p['assignments']),[])
                self.assertEqual(len({a['volunteer_id'] for a in p['assignments']}),9)
    def test_first_cancellation_covered_second_leaves_gap(self):
        for city in ['Chicago','Mumbai']:
            p=event(city);before=deepcopy(p)
            first=next(a['volunteer_id'] for a in p['assignments'] if a['shift_id']=='s1')
            p=cancellation_proposal(p,first)
            self.assertEqual(len(before['volunteers']),12)
            self.assertEqual(len(p['volunteers']),11)
            self.assertEqual(validate(p['volunteers'],p['shifts'],p['assignments']),[])
            second=next(a['volunteer_id'] for a in p['assignments'] if a['shift_id']=='s1')
            p=cancellation_proposal(p,second)
            self.assertEqual(len(p['volunteers']),10)
            issues=validate(p['volunteers'],p['shifts'],p['assignments'])
            self.assertEqual(len(issues),1)
            self.assertIn('short by 1',issues[0])
    def test_increased_headcount_does_not_invent_people(self):
        p=event('Chicago');p['shifts'][0]['required']=5
        a=schedule(p['volunteers'],p['shifts'])
        self.assertEqual(sum(x['shift_id']=='s1' for x in a),4)
        self.assertIn('short by 1',validate(p['volunteers'],p['shifts'],a)[0])
    def test_partial_availability_and_overlap(self):
        p=event('Chicago');p['volunteers'][0]['available_start']='10:30'
        a=schedule(p['volunteers'],p['shifts'])
        self.assertFalse(any(x['volunteer_id']=='v1' for x in a))
        p['shifts'].append(dict(id='s4',label='Extra entrance',start='11:00',end='13:00',required=1))
        issues=validate(p['volunteers'],p['shifts'],[dict(volunteer_id='v2',shift_id='s1'),dict(volunteer_id='v2',shift_id='s4')])
        self.assertTrue(any('double-booked' in x for x in issues))
        self.assertTrue(any('unavailable' in x for x in issues))
        self.assertTrue(any('maximum' in x for x in issues))
    def test_city_reminders_and_save_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            store=EventStore(directory=d)
            for city in ['Chicago','Mumbai']:
                p=event(city);p['tasks']=[dict(id='t1',title='Check signs',owner_id='v1',deadline=p['date'],done=True)]
                store.save(p)
                text=template_messages(p['event'],p['date'],p['location'],p['volunteers'],p['shifts'],p['assignments'])
                self.assertIn(p['date'],text);self.assertIn(p['location'],text)
                self.assertNotIn('Chicago' if city=='Mumbai' else 'Mumbai',text)
            saved=store.list()
            self.assertEqual(len(saved),2)
            self.assertTrue(all(p['tasks'][0]['done'] for p in saved))
            self.assertTrue(all(len(p['assignments'])==9 for p in saved))

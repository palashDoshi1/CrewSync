import unittest
from coordinator import *

class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.v = parse_csv(VOLUNTEERS, 'volunteers')
        self.s = parse_csv(SHIFTS, 'shifts')
    def test_demo_is_filled_and_valid(self):
        a = schedule(self.v, self.s)
        self.assertEqual(len(a), 6)
        self.assertEqual(validate(self.v, self.s, a), [])
    def test_overlap_availability_limit_duplicate_unknown_and_gap(self):
        shifts = parse_csv('id,label,start,end,required\ns1,Desk,10:00,12:00,1\ns2,Booth,11:00,13:00,1', 'shifts')
        v = parse_csv('id,name,available_start,available_end,max_shifts\nv1,Avery,10:00,12:00,1', 'volunteers')
        a = [{'volunteer_id':'v1','shift_id':sid} for sid in ['s1','s2','s1','missing']]
        issues = ' '.join(validate(v, shifts, a))
        for expected in ['double-booked','unavailable','maximum','Duplicate','Unknown']:
            self.assertIn(expected, issues)
        self.assertTrue(any('short by' in x for x in validate(v, shifts, schedule(v, shifts))))
    def test_adjacent_shifts_do_not_overlap(self):
        self.assertFalse(overlaps(self.s[0], self.s[1]))
    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            parse_csv(VOLUNTEERS + 'v1,Other,10:00,16:00,2\n','volunteers')
        with self.assertRaises(ValueError):
            parse_csv(SHIFTS.replace('10:00','18:00'), 'shifts')
    def test_unstaffable_plan(self):
        for v in self.v:
            v['available_end'] = '11:00'
        self.assertEqual(schedule(self.v, self.s), [])
        self.assertEqual(len(validate(self.v, self.s, [])), 3)

if __name__ == '__main__':
    unittest.main()

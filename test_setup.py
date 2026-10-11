import unittest
from setup_ui import sample_tables, read_tables
from coordinator import schedule, validate

class FriendlyInputs(unittest.TestCase):
    def test_samples_and_generated_ids(self):
        people, jobs = sample_tables()
        vs, ss = read_tables(people, jobs)
        self.assertEqual(validate(vs, ss, schedule(vs, ss)), [])
        self.assertEqual(vs[0]['id'], 'v1')
    def test_incomplete_row_explains_fix(self):
        people, jobs = sample_tables()
        people.loc[0, 'Name'] = ''
        with self.assertRaisesRegex(ValueError, 'Volunteer row 1'):
            read_tables(people, jobs)
    def test_bad_time_and_empty_table(self):
        people, jobs = sample_tables()
        jobs.at[0,'Ends'] = jobs.at[0,'Starts']
        with self.assertRaisesRegex(ValueError,'start must precede end'):
            read_tables(people, jobs)
        with self.assertRaisesRegex(ValueError,'at least one'):
            read_tables(people.iloc[:0],jobs)
    def test_fractional_count_rejected(self):
        people, jobs = sample_tables()
        jobs['People needed'] = jobs['People needed'].astype(float)
        jobs.at[0,'People needed'] = 1.5
        with self.assertRaisesRegex(ValueError,'whole number'):
            read_tables(people,jobs)

"""Friendly table inputs mapped to internal scheduling records."""
from datetime import datetime, time
import pandas as pd
from coordinator import parse_csv, VOLUNTEERS, SHIFTS, as_csv


def sample_tables():
    volunteers = parse_csv(VOLUNTEERS, 'volunteers')
    shifts = parse_csv(SHIFTS, 'shifts')
    clock = lambda s: datetime.strptime(s, '%H:%M').time()
    people = pd.DataFrame([{'Name':v['name'], 'Available from':clock(v['available_start']),
        'Available until':clock(v['available_end']), 'Maximum shifts':v['max_shifts']} for v in volunteers])
    jobs = pd.DataFrame([{'Shift / task':s['label'], 'Starts':clock(s['start']),
        'Ends':clock(s['end']), 'People needed':s['required']} for s in shifts])
    return people, jobs


def read_tables(people, jobs):
    def clock(value, row, label):
        if not isinstance(value, time):
            raise ValueError(f'{row}: choose a time for {label}.')
        return value.strftime('%H:%M')
    def name(value, row):
        if pd.isna(value) or not str(value).strip():
            raise ValueError(f'{row}: add a name, or delete the unused row.')
        return str(value).strip()
    def count(value, row):
        if pd.isna(value) or not 1 <= float(value) <= 100 or float(value) != int(value):
            raise ValueError(f'{row}: enter a whole number from 1 to 100.')
        return int(value)
    vs, ss = [], []
    for i, v in enumerate(people.to_dict('records'), 1):
        label = f'Volunteer row {i}'
        vs.append(dict(id=f'v{i}', name=name(v['Name'],label),
            available_start=clock(v['Available from'],label,'Available from'),
            available_end=clock(v['Available until'],label,'Available until'),
            max_shifts=count(v['Maximum shifts'],label)))
    for i, s in enumerate(jobs.to_dict('records'), 1):
        label = f'Shift row {i}'
        ss.append(dict(id=f's{i}', label=name(s['Shift / task'],label),
            start=clock(s['Starts'],label,'Starts'), end=clock(s['Ends'],label,'Ends'),
            required=count(s['People needed'],label)))
    if not vs or not ss:
        raise ValueError('Add at least one volunteer and one shift to get started.')
    # Reuse the scheduler's validation, including same-day time windows.
    return parse_csv(as_csv(vs),'volunteers'), parse_csv(as_csv(ss),'shifts')

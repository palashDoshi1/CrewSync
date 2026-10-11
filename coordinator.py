"""Deterministic scheduling and independent conflict validation. Same-day times only."""
import csv
import io
from collections import Counter
from datetime import datetime

VOLUNTEERS = '''id,name,available_start,available_end,max_shifts
v1,Avery,10:00,16:00,2
v2,Jordan,10:00,14:00,2
v3,Sam,12:00,16:00,2
v4,Riley,10:00,16:00,2
v5,Casey,10:00,12:00,1
v6,Morgan,14:00,16:00,1
'''
SHIFTS = '''id,label,start,end,required
s1,Welcome desk,10:00,12:00,2
s2,Fundraising booth,12:00,14:00,2
s3,Cleanup crew,14:00,16:00,2
'''

def minutes(value):
    t = datetime.strptime(str(value).strip(), '%H:%M')
    return t.hour * 60 + t.minute

def parse_csv(text, kind):
    fields = {'volunteers': ['id','name','available_start','available_end','max_shifts'],
              'shifts': ['id','label','start','end','required']}[kind]
    reader = csv.DictReader(io.StringIO(text.strip()))
    if reader.fieldnames != fields:
        raise ValueError(f'{kind} columns must be: {",".join(fields)}')
    rows = list(reader)
    if not rows or len(rows) > 100:
        raise ValueError(f'Provide 1–100 {kind}.')
    ids = set()
    for row in rows:
        if None in row or any(row.get(f) is None or not str(row[f]).strip() for f in fields):
            raise ValueError('Every row needs all columns. Quote names containing commas.')
        for f in fields:
            row[f] = row[f].strip()
        if row['id'] in ids:
            raise ValueError(f'Duplicate ID: {row["id"]}')
        ids.add(row['id'])
        a, b, n = ('available_start','available_end','max_shifts') if kind == 'volunteers' else ('start','end','required')
        if minutes(row[a]) >= minutes(row[b]):
            raise ValueError(f'{row["id"]}: start must precede end (same day).')
        row[n] = int(row[n])
        if not 1 <= row[n] <= 100:
            raise ValueError(f'{n} must be between 1 and 100.')
    return rows

def overlaps(a, b):
    return minutes(a['start']) < minutes(b['end']) and minutes(b['start']) < minutes(a['end'])

def schedule(volunteers, shifts):
    """Greedy, scarce-shift-first allocator; never relax constraints to fill a gap."""
    assigned = {v['id']: [] for v in volunteers}
    counts = Counter()
    def eligible(v, s):
        return minutes(v['available_start']) <= minutes(s['start']) and minutes(v['available_end']) >= minutes(s['end'])
    result = []
    for s in sorted(shifts, key=lambda s: (sum(eligible(v, s) for v in volunteers), minutes(s['start']), s['id'])):
        candidates = sorted(volunteers, key=lambda v: (counts[v['id']], v['id']))
        taken = 0
        for v in candidates:
            if taken >= s['required']:
                break
            if eligible(v, s) and counts[v['id']] < v['max_shifts'] and not any(overlaps(s, old) for old in assigned[v['id']]):
                result.append({'volunteer_id': v['id'], 'shift_id': s['id']})
                assigned[v['id']].append(s)
                counts[v['id']] += 1
                taken += 1
    return result

def validate(volunteers, shifts, assignments):
    vs, ss = {v['id']: v for v in volunteers}, {s['id']: s for s in shifts}
    issues, seen, valid = [], set(), []
    for a in assignments:
        vid, sid = a.get('volunteer_id'), a.get('shift_id')
        if vid not in vs or sid not in ss:
            issues.append('Unknown volunteer or shift ID in an assignment.')
            continue
        pair = (vid, sid)
        if pair in seen:
            issues.append(f'Duplicate assignment: {vs[vid]["name"]} / {ss[sid]["label"]}.')
            continue
        seen.add(pair)
        valid.append(a)
        v, s = vs[vid], ss[sid]
        if minutes(v['available_start']) > minutes(s['start']) or minutes(v['available_end']) < minutes(s['end']):
            issues.append(f'{v["name"]} is unavailable for {s["label"]}.')
    for vid, v in vs.items():
        booked = [ss[a['shift_id']] for a in valid if a['volunteer_id'] == vid]
        if len(booked) > v['max_shifts']:
            issues.append(f'{v["name"]} exceeds their maximum shifts.')
        for i, a in enumerate(booked):
            for b in booked[i+1:]:
                if overlaps(a, b):
                    issues.append(f'{v["name"]} is double-booked: {a["label"]} and {b["label"]}.')
    for sid, s in ss.items():
        count = sum(a['shift_id'] == sid for a in valid)
        if count < s['required']:
            issues.append(f'{s["label"]}: short by {s["required"] - count} volunteer(s).')
        elif count > s['required']:
            issues.append(f'{s["label"]}: overstaffed by {count - s["required"]}.')
    return issues

def display_rows(volunteers, shifts, assignments):
    vs, ss = {v['id']: v for v in volunteers}, {s['id']: s for s in shifts}
    return [{'Volunteer': vs[a['volunteer_id']]['name'], 'Shift': ss[a['shift_id']]['label'],
             'Start': ss[a['shift_id']]['start'], 'End': ss[a['shift_id']]['end'], **a} for a in assignments]

def as_csv(rows, fields=None):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields or list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()

def template_messages(event, date, location, volunteers, shifts, assignments):
    rows = display_rows(volunteers, shifts, assignments)
    return '\n\n'.join(f'Hi {v["name"]}! Thanks for helping at {event} on {date} at {location}. Your shifts: ' +
        '; '.join(f'{r["Shift"]} ({r["Start"]}–{r["End"]})' for r in rows if r['volunteer_id'] == v['id']) +
        '. Please reply to confirm, or let the coordinator know if your availability changes.'
        for v in volunteers if any(r['volunteer_id'] == v['id'] for r in rows))

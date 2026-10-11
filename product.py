"""Validated planning proposals and coordinator-controlled actions."""
import json
from copy import deepcopy
from datetime import date
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from coordinator import as_csv, parse_csv, schedule, validate

ZONES = ['America/New_York','America/Chicago','America/Denver','America/Los_Angeles','Europe/London','Asia/Kolkata','UTC']

def new_plan(event, day, location, volunteers, shifts, previous=None):
    previous = previous or {}
    old_names={v['id']:v['name'] for v in previous.get('volunteers',[])}
    tasks=deepcopy(previous.get('tasks',[]))
    for task in tasks:
        candidates=[v['id'] for v in volunteers if v['name']==old_names.get(task['owner_id'])]
        task['owner_id']=candidates[0] if len(candidates)==1 else ''
    return dict(id=previous.get('id',str(uuid4())), event=event, date=str(day), location=location,
        volunteers=volunteers, shifts=shifts, assignments=schedule(volunteers,shifts),
        tasks=tasks, announcement=previous.get('announcement',''))

def validate_proposal(raw, volunteers):
    if isinstance(raw,str):
        raw = raw.strip()
        if raw.startswith('```'):
            lines = raw.splitlines()
            raw = '\n'.join(lines[1:-1])
        raw = json.loads(raw)
    if not isinstance(raw,dict):
        raise ValueError('The AI plan must be a JSON object.')
    result = {}
    for field in ['event','date','location','timezone','announcement']:
        if not isinstance(raw.get(field),str) or not raw[field].strip() or len(raw[field])>4000:
            raise ValueError(f'The plan needs a valid {field}.')
        result[field] = raw[field].strip()
    date.fromisoformat(result['date'])
    try:
        ZoneInfo(result['timezone'])
    except ZoneInfoNotFoundError as exc:
        raise ValueError('The plan has an unknown time zone.') from exc
    shifts = raw.get('shifts')
    if not isinstance(shifts,list) or not 1<=len(shifts)<=30:
        raise ValueError('The plan needs 1–30 shifts.')
    normalized = []
    for i,s in enumerate(shifts,1):
        if not isinstance(s,dict) or not isinstance(s.get('label'),str) or not s['label'].strip():
            raise ValueError('Every proposed shift needs a label.')
        n = s.get('required')
        if isinstance(n,bool) or not isinstance(n,int):
            raise ValueError('People needed must be a whole number.')
        normalized.append(dict(id=f's{i}',label=s['label'].strip(),start=s.get('start'),end=s.get('end'),required=n))
    result['shifts'] = parse_csv(as_csv(normalized), 'shifts')
    tasks = raw.get('tasks',[])
    if not isinstance(tasks,list) or len(tasks)>40:
        raise ValueError('The plan allows up to 40 tasks.')
    known = {v['id'] for v in volunteers}
    result['tasks'] = []
    for i,t in enumerate(tasks,1):
        if not isinstance(t,dict) or not isinstance(t.get('title'),str) or not t['title'].strip():
            raise ValueError('Every task needs a title.')
        owner = t.get('owner_id','') or ''
        if owner and owner not in known:
            raise ValueError('A proposed task refers to an unknown volunteer.')
        deadline = t.get('deadline',result['date'])
        date.fromisoformat(deadline)
        result['tasks'].append(dict(id=f't{i}',title=t['title'].strip(),owner_id=owner,deadline=deadline,done=False))
    return result

def demo_proposal(today):
    return dict(event='Campus Giving Day',date=str(today),location='HUB entrance',timezone='America/New_York',
        shifts=[dict(label='Welcome desk',start='10:00',end='12:00',required=2),
                dict(label='Fundraising booth',start='12:00',end='14:00',required=2),
                dict(label='Cleanup crew',start='14:00',end='16:00',required=2)],
        tasks=[dict(title='Confirm the meeting point',owner_id='',deadline=str(today)),
               dict(title='Prepare check-in materials',owner_id='',deadline=str(today)),
               dict(title='Confirm volunteer availability',owner_id='',deadline=str(today))],
        announcement='Join us for Campus Giving Day at the HUB entrance. Check your assigned shift and confirm your availability with the coordinator.')

def cancellation_proposal(plan, volunteer_id):
    if volunteer_id not in {v['id'] for v in plan['volunteers']}:
        raise ValueError('Choose a volunteer from this event.')
    proposal = deepcopy(plan)
    proposal['volunteers'] = [v for v in plan['volunteers'] if v['id'] != volunteer_id]
    if not proposal['volunteers']:
        # Empty roster is allowed for cancellation recovery, and all coverage is flagged.
        proposal['assignments'] = []
    else:
        proposal['assignments'] = schedule(proposal['volunteers'],proposal['shifts'])
    for task in proposal.get('tasks',[]):
        if task['owner_id']==volunteer_id:
            task['owner_id']=''
    return proposal

def recovery_candidates(plan):
    """One candidate per shift suggestion; proposals are not simultaneous assignments."""
    from coordinator import minutes, overlaps
    result=[]
    for s in plan['shifts']:
        booked = sum(a['shift_id']==s['id'] for a in plan['assignments'])
        if booked>=s['required']: continue
        for v in plan['volunteers']:
            current=[next(x for x in plan['shifts'] if x['id']==a['shift_id']) for a in plan['assignments'] if a['volunteer_id']==v['id']]
            if len(current)<v['max_shifts'] and minutes(v['available_start'])<=minutes(s['start']) and minutes(v['available_end'])>=minutes(s['end']) and not any(overlaps(s,x) for x in current):
                result.append(dict(volunteer=v['name'],shift=s['label'],start=s['start'],end=s['end']))
    return result

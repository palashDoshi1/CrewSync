"""Workspace UI for saved events, planning proposals and coordinator actions."""
import json
from copy import deepcopy
from datetime import date, datetime
from uuid import uuid4
import pandas as pd
import streamlit as st
from product import ZONES, demo_proposal, validate_proposal, new_plan, cancellation_proposal, recovery_candidates
from coordinator import validate, display_rows, template_messages
from setup_ui import sample_tables
from ai_client import create_event, draft_messages


def clear_outputs():
    for k in ('draft','draft_source','briefing','briefing_source','outreach','cancel_preview'):
        st.session_state.pop(k,None)

def seed_plan(plan):
    st.session_state.pending_seed=deepcopy(plan)

def apply_pending():
    if 'pending_seed' not in st.session_state:
        return
    plan=st.session_state.pop('pending_seed')
    st.session_state.plan=deepcopy(plan)
    clear_outputs()
    meeting, _, zone = plan['location'].rpartition(' · ')
    if not meeting:
        meeting, zone = plan['location'], 'America/New_York'
    st.session_state['event_name']=plan['event']
    st.session_state['event_day']=date.fromisoformat(plan['date'])
    st.session_state['event_location']=meeting
    st.session_state['event_zone']=zone
    st.session_state['setup_source']=deepcopy(plan)
    st.session_state['setup_revision']=st.session_state.get('setup_revision',0)+1

def setup_tables():
    p=st.session_state.get('setup_source')
    if not p: return sample_tables()
    clock=lambda s:datetime.strptime(s,'%H:%M').time()
    people=pd.DataFrame([{'Name':v['name'],'Available from':clock(v['available_start']), 'Available until':clock(v['available_end']),'Maximum shifts':v['max_shifts']} for v in p['volunteers']],columns=['Name','Available from','Available until','Maximum shifts'])
    jobs=pd.DataFrame([{'Shift / task':s['label'],'Starts':clock(s['start']),'Ends':clock(s['end']),'People needed':s['required']} for s in p['shifts']],columns=['Shift / task','Starts','Ends','People needed'])
    return people,jobs

def library(store):
    with st.expander('Your event dashboard · save, reopen, and track progress',expanded=True):
        st.caption('Local library stays on this computer. MongoDB stores approved event snapshots in your configured database. Click Save to persist changes.')
        if st.button('Save current event',disabled='plan' not in st.session_state):
            try:
                store.save(st.session_state.plan)
                st.success('Event saved, including volunteers, assignments and tasks.')
            except Exception as exc:
                st.error(f'Save failed ({type(exc).__name__}). Your event remains in this session. Check storage settings.')
        try:
            events=store.list()
        except Exception as exc:
            events=[]
            st.error(f'Could not load events ({type(exc).__name__}). Check the database connection and Atlas network access.')
        if events:
            upcoming=sum(date.fromisoformat(p['date'])>=date.today() for p in events)
            gaps=sum(sum('short by' in x for x in validate(p['volunteers'],p['shifts'],p['assignments'])) for p in events)
            pending=sum(sum(not t['done'] for t in p.get('tasks',[])) for p in events)
            a,b,c=st.columns(3)
            a.metric('Upcoming events',upcoming); b.metric('Shifts needing help',gaps); c.metric('Open tasks',pending)
            st.dataframe([{'Event':p['event'],'Date':p['date'],'Volunteers':len(p['volunteers']),'Tasks complete':f"{sum(t['done'] for t in p.get('tasks',[]))}/{len(p.get('tasks',[]))}"} for p in events],hide_index=True,width='stretch')
            selected=st.selectbox('Saved event',list(range(len(events))),format_func=lambda i:f"{events[i]['event']} · {events[i]['date']} · {events[i]['id'][:6]}")
            if st.button('Open selected event'):
                seed_plan(events[selected])
                st.rerun()
        else:
            st.info('Create your first event below, then Save current event to keep it here.')
            if st.button('Use this roster for a new event'):
                from coordinator import parse_csv, SHIFTS
                selected_roster=deepcopy(events[selected]['volunteers'])
                p=new_plan('New volunteer event',date.today(),'Meeting point · America/New_York',selected_roster,parse_csv(SHIFTS,'shifts'))
                seed_plan(p)
                st.rerun()
        if st.button('Start a new sample event'):
            from setup_ui import read_tables
            vs,ss=read_tables(*sample_tables())
            p=new_plan('Campus Giving Day',date.today(),'HUB entrance · America/New_York',vs,ss)
            seed_plan(p)
            st.rerun()

def event_creator(key,base,model,mode):
    with st.expander('Describe your event · let the AI draft the plan',expanded=True):
        description=st.text_area('What are you organizing?',placeholder='A campus food drive next Saturday, 10 AM–4 PM at the HUB. We need check-in, packing and cleanup teams.',height=100)
        st.caption('Live mode drafts shifts, a checklist and an announcement. It uses your last created roster, or the sample roster before your first event. Suggested details need your review.')
        if st.button('Draft my event plan',disabled=not description.strip()):
            st.session_state.pop('event_proposal',None)
            st.session_state.pop('proposal_json',None)
            st.session_state.pop('proposal_approved',None)
            try:
                from setup_ui import read_tables
                vs=st.session_state.plan['volunteers'] if 'plan' in st.session_state else read_tables(*sample_tables())[0]
                if mode.startswith('Demo'):
                    proposal=validate_proposal(demo_proposal(date.today()),vs)
                    source='Sample fixture · no AI request · does not interpret your description'
                else:
                    with st.spinner('Drafting an editable event plan…'):
                        proposal=create_event(key,base,model,description,vs,date.today())
                    source=f'Live AI · {model}'
                st.session_state.event_proposal=dict(proposal=proposal,volunteers=deepcopy(vs),source=source)
            except Exception as exc:
                st.error(f'Could not create a valid plan ({type(exc).__name__}). Check the AI settings and try again. Your event is unchanged.')
        if 'event_proposal' in st.session_state:
            pending=st.session_state.event_proposal
            st.caption(pending['source'])
            proposal=pending['proposal']
            st.write(f"**{proposal['event']}** · {proposal['date']} · {proposal['location']}")
            st.dataframe(proposal['shifts'],hide_index=True,width='stretch')
            st.write('Suggested checklist: '+ '; '.join(t['title'] for t in proposal['tasks']))
            st.text(proposal['announcement'])
            with st.expander('Advanced · edit the proposal JSON'):
                edited=st.text_area('Editable proposal',json.dumps(proposal,indent=2),height=220,key='proposal_json')
            approved=st.checkbox('I have reviewed the date, place, shifts and suggested tasks.',key='proposal_approved')
            if st.button('Approve & create event',disabled=not approved,type='primary'):
                try:
                    reviewed=validate_proposal(edited,pending['volunteers'])
                    p=new_plan(reviewed['event'],reviewed['date'],reviewed['location']+' · '+reviewed['timezone'],pending['volunteers'],reviewed['shifts'])
                    p.update(tasks=reviewed['tasks'],announcement=reviewed['announcement'])
                    seed_plan(p)
                    st.session_state.pop('event_proposal',None)
                    st.session_state.pop('proposal_approved',None)
                    st.rerun()
                except (ValueError,TypeError,KeyError) as exc:
                    st.error(f'Please fix the proposal: {exc}')

def task_manager(p):
    st.subheader('Event checklist')
    tasks=p.get('tasks',[])
    total=len(tasks); complete=sum(t['done'] for t in tasks)
    st.progress(complete/total if total else 0,text=f'{complete} of {total} tasks complete')
    owners={'Unassigned':''}
    owners.update({f"{v['name']} · {v['id']}":v['id'] for v in p['volunteers']})
    labels={v:k for k,v in owners.items()}
    data=pd.DataFrame([dict(id=t['id'],Task=t['title'],Owner=labels.get(t['owner_id'],'Unassigned'),Due=date.fromisoformat(t['deadline']),Done=t['done']) for t in tasks],columns=['id','Task','Owner','Due','Done'])
    with st.form('task_form_'+p['id']):
        edited=st.data_editor(data,num_rows='dynamic',hide_index=True,width='stretch',key='task_editor_'+p['id']+'_'+str(st.session_state.get('task_revision',0)),column_config={
            'id':None,
            'Task':st.column_config.TextColumn('Task',required=True),
            'Owner':st.column_config.SelectboxColumn('Responsible person',options=list(owners),default='Unassigned',required=True),
            'Due':st.column_config.DateColumn('Due date',default=date.fromisoformat(p['date']),required=True),
            'Done':st.column_config.CheckboxColumn('Complete',default=False,required=True),
        })
        if st.form_submit_button('Update checklist'):
            try:
                out=[]
                if len(edited)>100: raise ValueError('Keep the checklist to 100 tasks.')
                for row in edited.to_dict('records'):
                    if pd.isna(row['Task']) or not str(row['Task']).strip() or row['Owner'] not in owners or pd.isna(row['Due']):
                        raise ValueError('Each task needs a title, owner (or Unassigned) and date.')
                    old_id=row['id']
                    out.append(dict(id=str(uuid4()) if pd.isna(old_id) else str(old_id),title=str(row['Task']).strip(),owner_id=owners[row['Owner']],deadline=str(row['Due']),done=bool(row['Done'])))
                p['tasks']=out
                st.session_state.task_revision=st.session_state.get('task_revision',0)+1
                st.rerun()
            except (ValueError,TypeError) as exc:
                st.error(str(exc))
    st.caption('Checklist edits are local to this event. Save current event to keep your changes between sessions.')

def recovery(p,key,base,model,mode):
    with st.expander('Cancellation recovery · rebalance the crew'):
        ids=[v['id'] for v in p['volunteers']]
        names={v['id']:v['name'] for v in p['volunteers']}
        if ids:
            chosen=st.selectbox('Who can no longer help?',ids,format_func=lambda x:names[x])
            if 'cancel_preview' in st.session_state and st.session_state.get('cancel_preview_for') != chosen:
                st.session_state.pop('cancel_preview',None)
                st.session_state.pop('cancel_approval',None)
            if st.button('Preview cancellation & new schedule'):
                st.session_state.pop('cancel_approval',None)
                st.session_state.cancel_preview_for=chosen
                st.session_state.cancel_preview=cancellation_proposal(p,chosen)
            if 'cancel_preview' in st.session_state:
                proposed=st.session_state.cancel_preview
                st.dataframe(display_rows(proposed['volunteers'],proposed['shifts'],proposed['assignments']),hide_index=True,width='stretch')
                for issue in validate(proposed['volunteers'],proposed['shifts'],proposed['assignments']):st.warning(issue)
                st.write(f'Proposed cancellation: **{names[chosen]}**')
                st.caption('Applying removes this volunteer from this event, clears their checklist responsibilities, and replaces the assignments shown above. No messages are sent.')
                approved=st.checkbox('Approve this roster and assignment change',key='cancel_approval')
                if st.button('Apply cancellation plan',disabled=not approved):
                    seed_plan(proposed)
                    st.session_state.pop('cancel_approval',None)
                    st.rerun()
        candidates=recovery_candidates(p)
        if st.button('Prepare requests for uncovered shifts'):
            issues=validate(p['volunteers'],p['shifts'],p['assignments'])
            if mode.startswith('Demo'):
                if candidates:
                    text='\n\n'.join(f"Hi {c['volunteer']}, could you help with {c['shift']} from {c['start']} to {c['end']} at {p['event']} on {p['date']}? Please confirm with the coordinator before joining." for c in candidates)
                else:
                    text='No unassigned volunteers fit the remaining gaps under the current constraints. Recruit more help or review availability and shift requirements.' if any('short by' in x for x in issues) else 'All shifts are covered. No extra outreach is needed.'
                st.session_state.outreach='Local analysis and templates · no AI request\n\n'+text
            else:
                try:
                    with st.spinner('Drafting targeted requests…'):
                        st.session_state.outreach='Live AI · '+model+'\n\n'+draft_messages(key,base,model,dict(event=p['event'],date=p['date'],location=p['location'],validated_issues=issues,candidates=candidates),purpose='outreach')
                except Exception as exc:
                    st.error(f'Outreach failed ({type(exc).__name__}).')
        if 'outreach' in st.session_state:
            st.text(st.session_state.outreach)
            st.caption('Candidates are individual suggestions, not simultaneous assignments. Review requests and wait for volunteer confirmation.')
            st.download_button('Download help requests',st.session_state.outreach,'crewsync-help-requests.txt','text/plain')

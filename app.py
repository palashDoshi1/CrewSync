import os
from datetime import date, time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from coordinator import VOLUNTEERS, SHIFTS, parse_csv, schedule, validate, display_rows, as_csv, template_messages
from ai_client import draft_messages, LUMINAL_BASE_URL, LUMINAL_MODEL, safe_error
from ui import apply_theme, hero, shift_cards
from setup_ui import sample_tables, read_tables
from workspace import library, event_creator, setup_tables, task_manager, recovery, clear_outputs, apply_pending
from product import new_plan, ZONES
from storage import EventStore, SessionEventStore

load_dotenv(Path(__file__).with_name('.env'))
st.set_page_config(page_title='CrewSync AI', page_icon='👥', layout='wide')
apply_pending()
public_demo = os.getenv("CREWSYNC_PUBLIC_DEMO", "").lower() == "true"

with st.sidebar:
    st.title('CrewSync AI')
    st.caption('Your volunteer coordination workspace')
    theme = st.radio('Color theme', ['Midnight', 'Daylight'], horizontal=True)
    motion = st.toggle('Subtle animations', value=True)
    st.divider()
    st.header('AI connection')
    mode = st.radio('Message drafting', ['Demo · local templates', 'Luminal · live AI'])
    with st.expander('Private AI settings · collapse for recording', expanded=False):
        key = st.text_input('API key', value='' if public_demo else os.getenv('LUMINAL_API_KEY', ''), type='password')
        base = st.text_input('API base URL', value=os.getenv('LUMINAL_BASE_URL') or LUMINAL_BASE_URL, help='Copy the documented OpenAI-compatible base URL. Include any version path required by Luminal.')
        model = st.text_input('Model ID', value=os.getenv('LUMINAL_MODEL') or LUMINAL_MODEL)
    st.caption('Live drafting sends the event, volunteer names and assigned shifts to your configured provider. No messages are sent to volunteers.')
    st.info('Scheduling and conflict checks work without an API key.')
    st.divider()
    with st.expander('Database connection'):
        uri = st.text_input('MongoDB connection URI',value='' if public_demo else os.getenv('MONGODB_URI',''),type='password',help='Enter your Atlas URI here or in the local .env file. It includes your database password.')
    backend = st.radio('Event storage', ['Local library', 'MongoDB Atlas'], help='Atlas requires MONGODB_URI in the local .env file.')
    if backend == 'MongoDB Atlas' and not uri:
        st.warning('Add MONGODB_URI to .env and restart. Local storage is active until then.')
    if public_demo:
        st.session_state.setdefault('private_demo_events',{})
        store = SessionEventStore(st.session_state.private_demo_events)
        st.caption('Hosted demo: saved events belong to this browser session. MongoDB is not used.')
    else:
        store = EventStore(uri=uri if backend == 'MongoDB Atlas' else '', database=os.getenv('MONGODB_DATABASE','crewsync'),directory=os.getenv('CREWSYNC_DATA_DIR') or None)

apply_theme(theme, motion)
hero()
with st.expander('Watch the one-minute CrewSync overview'):
    video_path=Path(__file__).parent/'media'/'crewsync-demo.mp4'
    if video_path.exists():
        st.video(str(video_path))
        st.caption('Narrated animated explainer using fictional data. MongoDB is optional and not used in this demo.')
library(store)
event_creator(key,base,model,mode)
st.subheader('Bring your event together')
st.caption('Start with our sample event. Click any cell to make it yours — no special formatting needed.')
people_default, shifts_default = setup_tables()
for field, value in dict(event_name='Campus Giving Day',event_day=date.today(),event_location='HUB entrance',event_zone='America/New_York').items():
    st.session_state.setdefault(field,value)
revision=st.session_state.get('setup_revision',0)
with st.form('event'):
    st.markdown('#### 1 · The basics')
    c1, c2 = st.columns([2, 1])
    event = c1.text_input('What is your event called?', key='event_name', placeholder='e.g. Food drive, THON fundraiser, campus cleanup')
    event_date = c2.date_input('When is it happening?', key='event_day')
    c1, c2 = st.columns([2, 1])
    location_name = c1.text_input('Where should people meet?', key='event_location', placeholder='Building, room, or meeting point')
    zone = c2.selectbox('Time zone', list(dict.fromkeys(ZONES+[st.session_state.event_zone])), key='event_zone', help='All availability and shift times use this time zone.')
    location = location_name + ' · ' + zone
    st.markdown('#### 2 · Who is helping?')
    st.caption('Add a name and the hours they can help. Maximum shifts limits how many tasks they receive.')
    people = st.data_editor(people_default, num_rows='dynamic', hide_index=True, width='stretch', key='people_editor_'+str(revision), column_config={
        'Name': st.column_config.TextColumn('Volunteer name', required=True, help='First name is enough for this demo.'),
        'Available from': st.column_config.TimeColumn('Free from', format='h:mm a', step=60, required=True, default=time(10)),
        'Available until': st.column_config.TimeColumn('Free until', format='h:mm a', step=60, required=True, default=time(16)),
        'Maximum shifts': st.column_config.NumberColumn('Max. shifts', min_value=1, max_value=100, step=1, default=1, required=True),
    })
    st.markdown('#### 3 · What needs doing?')
    st.caption('Name each shift or task, choose its hours, and tell us how many people you need.')
    jobs = st.data_editor(shifts_default, num_rows='dynamic', hide_index=True, width='stretch', key='shifts_editor_'+str(revision), column_config={
        'Shift / task': st.column_config.TextColumn('Task or shift', required=True, help='e.g. Check-in desk, setup, cleanup'),
        'Starts': st.column_config.TimeColumn('Starts at', format='h:mm a', step=60, required=True, default=time(10)),
        'Ends': st.column_config.TimeColumn('Ends at', format='h:mm a', step=60, required=True, default=time(12)),
        'People needed': st.column_config.NumberColumn('People needed', min_value=1, max_value=100, step=1, default=1, required=True),
    })
    st.caption('Use the blank row to add people or tasks. Select a row to remove it. All shifts start and finish on your event date.')
    generate = st.form_submit_button('Create my schedule →', type='primary')
if generate:
    try:
        if not event.strip() or not location_name.strip():
            raise ValueError('Enter an event name and location.')
        volunteers, shifts = read_tables(people, jobs)
        old=st.session_state.get('plan')
        st.session_state.plan = new_plan(event,event_date,location,volunteers,shifts,previous=old)
        clear_outputs()
    except (ValueError, TypeError) as exc:
        st.error(f'Check your input: {exc}')

if 'plan' in st.session_state:
    p = st.session_state.plan
    st.subheader(f'{p["event"]} · {p["date"]}')
    st.caption('This is your last created plan. Changed a name or time? Click Create my schedule again to update it.')
    issues = validate(p['volunteers'], p['shifts'], p['assignments'])
    shift_cards(p)
    c1, c2, c3 = st.columns(3)
    c1.metric('Volunteers', len(p['volunteers']))
    c2.metric('Assignments', len(p['assignments']))
    c3.metric('Issues to resolve', len(issues))
    rows = display_rows(p['volunteers'], p['shifts'], p['assignments'])
    st.dataframe(rows, width='stretch', hide_index=True)
    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success('All shifts filled. No availability, overlap, or workload conflicts detected.')
    st.download_button('Download schedule CSV', as_csv(rows, ['Volunteer','Shift','Start','End','volunteer_id','shift_id']), 'crewsync-schedule.csv', 'text/csv')
    with st.expander('Check an existing assignment plan — try a double booking'):
        st.caption('Change IDs below, or upload an assignment CSV. This does not change the generated schedule.')
        uploaded = st.file_uploader('Assignment CSV', type=['csv'])
        proposed = st.text_area('Assignments to check', as_csv(p['assignments'], ['volunteer_id','shift_id']))
        if st.button('Check conflicts'):
            try:
                import csv, io
                text = uploaded.getvalue().decode('utf-8-sig') if uploaded else proposed
                reader = csv.DictReader(io.StringIO(text.strip()))
                if reader.fieldnames != ['volunteer_id','shift_id']:
                    raise ValueError('Columns must be volunteer_id,shift_id.')
                entries = list(reader)
                if any(None in a or any(not a.get(k) for k in ('volunteer_id','shift_id')) for a in entries):
                    raise ValueError('Every row must contain both IDs.')
                found = validate(p['volunteers'], p['shifts'], entries)
                if found:
                    for issue in found:
                        st.warning(issue)
                else:
                    st.success('All constraints pass.')
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
    task_manager(p)
    recovery(p,key,base,model,mode)
    if p.get('announcement'):
        st.subheader('Event announcement')
        announcement = st.text_area('Review announcement',p['announcement'],height=120,key='announcement_'+p['id'])
        st.download_button('Download announcement',announcement,'crewsync-announcement.txt','text/plain')
        if st.button('Keep edited announcement'):
            p['announcement']=announcement
            st.success('Announcement updated. Save current event to persist it.')
    st.subheader('Your AI copilot')
    st.caption('Plan the next move, then give every volunteer a clear reminder.')
    tone = st.selectbox('Communication style', ['Warm and concise', 'Professional and direct', 'Upbeat and encouraging'])
    if st.button('Create coordinator briefing'):
        st.session_state.pop('briefing', None)
        if mode.startswith('Demo'):
            coverage = '\n'.join('- ' + x for x in issues) if issues else '- Every shift is staffed within the supplied constraints.'
            st.session_state.briefing = ('## Coverage & risks\n' + coverage +
                '\n\n## Next actions\n- Review the shift plan and confirm availability with each volunteer.\n- Resolve any staffing gaps before sharing the schedule.\n\n## Event checklist · suggestions\n- Choose an on-site contact.\n- Prepare check-in instructions.\n- Agree on a cancellation and backup process.')
            st.session_state.briefing_source = 'Local checklist · no AI request'
        else:
            context = {k: p[k] for k in ('event', 'date', 'location')}
            context.update(assignments=rows, shifts=p['shifts'], validated_issues=issues)
            try:
                with st.spinner('Creating your event briefing…'):
                    st.session_state.briefing = draft_messages(key, base, model, context, purpose='briefing', tone=tone)
                st.session_state.briefing_source = f'Live AI · {model}'
            except Exception as exc:
                st.error(safe_error(exc))
    if 'briefing' in st.session_state:
        st.caption(st.session_state.briefing_source + ' · review AI suggestions before acting')
        st.markdown(st.session_state.briefing)
        st.download_button('Download event briefing', st.session_state.briefing, 'crewsync-briefing.md', 'text/markdown')
    st.subheader('Volunteer reminder drafts')
    if st.button('Draft reminders', disabled=not rows):
        st.session_state.pop('draft', None)
        if mode.startswith('Demo'):
            st.session_state.draft = template_messages(p['event'], p['date'], p['location'], p['volunteers'], p['shifts'], p['assignments'])
            st.session_state.draft_source = 'Local templates · no AI request'
        else:
            context = {k: p[k] for k in ('event', 'date', 'location')}
            context['assignments'] = rows
            try:
                with st.spinner('Luminal is drafting reminders…'):
                    st.session_state.draft = draft_messages(key, base, model, context, tone=tone)
                st.session_state.draft_source = f'Live AI · {model}'
            except Exception as exc:
                # Do not show raw provider errors, URLs or keys in the UI.
                kind = type(exc).__name__
                st.error(safe_error(exc))
    if 'draft' in st.session_state:
        st.caption(st.session_state.draft_source + ' · review names and times before sharing')
        edited = st.text_area('Draft text', st.session_state.draft, height=260, key='draft_editor_' + str(st.session_state.draft))
        st.download_button('Download reminders', edited, 'crewsync-reminders.txt', 'text/plain')
else:
    st.info('Ready when you are. Try the sample event, or edit the tables above, then click Create my schedule.')
st.caption('Built for volunteer coordinators & student organizers · Review your schedule and reminders before sharing.')

import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest

def button(at,name):return next(x for x in at.button if x.label==name)
def check(at):assert not at.exception,at.exception
with tempfile.TemporaryDirectory() as directory:
    os.environ['CREWSYNC_DATA_DIR']=directory
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20).run()
    check(at)
    button(at,'Create my schedule →').click().run();check(at)
    assert len(at.session_state.plan['assignments'])==6
    button(at,'Draft reminders').click().run();check(at)
    assert 'Local templates' in at.session_state.draft_source
    next(x for x in at.text_area if x.label=='What are you organizing?').set_value('A food drive with three teams.').run()
    button(at,'Draft my event plan').click().run();check(at)
    assert 'Sample fixture' in at.session_state.event_proposal['source']
    assert len(at.session_state.plan['tasks'])==0
    next(x for x in at.checkbox if x.label=='I have reviewed the date, place, shifts and suggested tasks.').check().run()
    button(at,'Approve & create event').click().run();check(at)
    assert len(at.session_state.plan['tasks'])==3
    # Complete a task through the editor's documented session-state delta.
    editor='task_editor_'+at.session_state.plan['id']+'_0'
    at.session_state[editor]={'edited_rows':{0:{'Done':True,'Owner':'Avery · v1'}},'added_rows':[],'deleted_rows':[]}
    button(at,'Update checklist').click().run();check(at)
    assert at.session_state.plan['tasks'][0]['done']
    assert at.session_state.plan['tasks'][0]['owner_id']=='v1'
    before=len(at.session_state.plan['volunteers'])
    button(at,'Preview cancellation & new schedule').click().run();check(at)
    assert len(at.session_state.plan['volunteers'])==before
    next(x for x in at.checkbox if x.label=='Approve this roster and assignment change').check().run()
    button(at,'Apply cancellation plan').click().run();check(at)
    assert len(at.session_state.plan['volunteers'])==before-1
    assert at.session_state.plan['tasks'][0]['owner_id']==''
    button(at,'Save current event').click().run();check(at)
    assert len(list(Path(directory).glob('*.json')))==1
    button(at,'Start a new sample event').click().run();check(at)
    assert len(at.session_state.plan['volunteers'])==6
    button(at,'Open selected event').click().run();check(at)
    assert len(at.session_state.plan['volunteers'])==5
    assert at.session_state.plan['tasks'][0]['done']
    button(at,'Use this roster for a new event').click().run();check(at)
    assert at.session_state.plan['event']=='New volunteer event'
    assert len(at.session_state.plan['volunteers'])==5
    next(x for x in at.radio if x.label=='Color theme').set_value('Daylight').run();check(at)
    next(x for x in at.text_input if x.label=='What is your event called?').set_value('')
    button(at,'Create my schedule →').click().run();check(at)
    assert at.error
    assert len(at.session_state.plan['volunteers'])==5 # keep last good plan on bad input
    print('Full workflow passed: planning approval, tasks, cancellation approval, persistence, reopen, themes, invalid-input recovery.')

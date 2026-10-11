"""Opt-in live Luminal smoke test. No secrets or raw provider responses printed."""
import os
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from ai_client import create_event,LUMINAL_BASE_URL,LUMINAL_MODEL
from test_scenarios import roster


def main():
    load_dotenv(Path(__file__).with_name('.env'))
    key=os.getenv('LUMINAL_API_KEY','')
    if not key.strip():
        print('Not run: add your key to the local .env or test through the app sidebar.')
        return 2
    try:
        plan=create_event(key,os.getenv('LUMINAL_BASE_URL') or LUMINAL_BASE_URL,os.getenv('LUMINAL_MODEL') or LUMINAL_MODEL,
            'Fictional Chicago football event October 16, 2026 at Stadium entrance, America/Chicago. Exactly three shifts: Welcome 10:00-12:00, Assistance 12:00-14:00, Cleanup 14:00-16:00. Three people per shift. Use only the supplied volunteers. Include a preparation checklist and announcement.',roster(),date.today())
        assert plan['date']=='2026-10-16' and plan['timezone']=='America/Chicago'
        assert [(s['start'],s['end'],s['required']) for s in plan['shifts']]==[('10:00','12:00',3),('12:00','14:00',3),('14:00','16:00',3)]
        print('PASS: live Luminal plan returned valid JSON, date, time zone and requested shifts. Review names and draft communication in the app.')
        return 0
    except Exception as exc:
        print(f'FAIL ({type(exc).__name__}): check credentials, model, credits and response format. Raw errors withheld to protect secrets.')
        return 1

if __name__=='__main__':
    raise SystemExit(main())

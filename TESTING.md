# Chicago football and Mumbai hackathon checks
All automated scenarios use synthetic volunteers and make no paid API calls.

Run:
```sh
python -m unittest discover -v
```

## Shared 12-person roster
Add each name as a separate volunteer with maximum shifts = 1.

| Names | Free from | Free until |
|---|---|---|
| Alex, Blair, Casey, Drew | 10:00 AM | 12:00 PM |
| Ellis, Finley, Gray, Harper | 12:00 PM | 2:00 PM |
| Jamie, Kai, Logan, Morgan | 2:00 PM | 4:00 PM |

Create a schedule once to establish the roster before asking the live AI to create an event.

## Chicago input
```text
Create a fictional football volunteer event at Chicago State University
on Friday, October 16, 2026. Meeting point: Stadium entrance.
Time zone: America/Chicago. Use only the existing 12 volunteers.
Create exactly three shifts, with three people on each:
Welcome and check-in 10:00–12:00; Guest assistance 12:00–14:00;
Cleanup 14:00–16:00. Suggest preparation tasks and an announcement.
Do not invent volunteers, confirmations, sponsors or links.
```

## Mumbai input
```text
Create a fictional university hackathon in Mumbai on Saturday,
October 17, 2026. Meeting point: Main auditorium entrance.
Time zone: Asia/Kolkata. Use only the existing 12 volunteers.
Create exactly three shifts, with three people on each:
Registration desk 10:00–12:00; Participant support 12:00–14:00;
Demo-room preparation 14:00–16:00. Suggest preparation tasks and
an announcement. Do not invent volunteers, prizes, sponsors or links.
```

## Expected results and recovery
- After reviewing the proposal and approving: 9 assignments, 3/3 coverage per shift, zero issues. Three people remain unassigned.
- Preview cancelling an assigned check-in/registration volunteer: the current plan must stay unchanged until approval.
- Approve first cancellation: 11 volunteers remain; the spare covers that shift; zero coverage gaps.
- Cancel another assigned person from that same shift: 10 volunteers remain; that shift has 2/3 coverage and a shortage of 1.
- A cancelled volunteer's checklist responsibilities become Unassigned.
- On a fresh roster, increase the first shift to five people: four eligible assignments and a shortage of 1.
- Change Alex's start to 10:30: Alex cannot cover 10:00–12:00.
- Assign one person to overlapping shifts in the advanced checker: overlap, availability and maximum-shift violations are reported as applicable.
- Save both events, open a different event, then reopen: city, time zone, roster, assignments and completed tasks remain correct.
- Reminders must preserve the active event's city, date and shift times.

The AI may propose different details; correct those before approval. Automated tests establish scheduler behavior for the explicit fixtures, not the reliability of every possible model response.

## Live Luminal checks
The settings shown in the user-provided dashboard are:
- Base URL: `https://flash.luminal.cloud/v1`
- Model: `deepseek-ai/DeepSeek-V4.1-Flash`

Enter the secret key in the sidebar, or your ignored local `.env`. Keep Private AI settings collapsed during recording. Never paste the key into this file or a GitHub issue.

Select Luminal · live AI. First generate reminders for a sample schedule, then test the two event prompts. Verify the Live AI label and check each result against the input. Invalid model IDs, unavailable credits and network failures must retain the last good event. There is no silent template fallback for live mode.

For an optional terminal smoke test with `.env` configured:
```sh
python live_check.py
```
This makes one real AI event-plan request (may use credits), validates its structure and reports only pass/fail. It never prints the key or raw provider error. Review the full generated result in the app before filming.

MongoDB is optional: local Save → Reopen works without it. Only claim Atlas persistence after repeating the test with Atlas selected and configured.

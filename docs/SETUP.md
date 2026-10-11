# CrewSync AI
**You lead. We coordinate.** A local-first coordination workspace for student clubs, THON committees and volunteer organizers.

## Run it
Python 3.10+ is required. Open this folder in a terminal:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Windows activation: `.venv\Scripts\activate`. Open the local URL printed by Streamlit, usually http://localhost:8501. Keep the terminal open. `requirements-lock.txt` captures the versions used in the development environment; the regular requirements file allows compatible updates.

## What works
- Friendly editable volunteer and task/shift tables, AM/PM time controls and automatically generated IDs.
- Availability-aware scheduling, overlap/workload checks, and visible staffing gaps.
- Natural-language event creation through an explicitly configured OpenAI-compatible chat model: editable proposals with suggested shifts, checklist and announcement. Python computes assignments after approval.
- Separate task checklist: assign responsibility, set due dates, and mark tasks complete.
- Saved-event dashboard: upcoming events, staffing gaps and task progress.
- Cancellation recovery: preview a revised roster/schedule, then approve before applying. Responsibilities belonging to the cancelled volunteer become unassigned.
- Coordinator briefings, reminder drafts, and requests for uncovered shifts.
- Local event persistence by default, or MongoDB Atlas when selected and configured.
- CSV/text exports, announcement drafts, and Midnight/Daylight themes with reduced-motion support.

The app does not send emails/texts, accept registrations, interact with third-party applications, or implement on-device inference. Announcements and messages are reviewed and downloaded for manual sharing. This demo is a coordinator tool, not a publicly hosted multi-user service.

## Connect Luminal
Copy `.env.example` to `.env`:

```sh
cp .env.example .env
```

Fill in:

```dotenv
LUMINAL_API_KEY=
LUMINAL_BASE_URL=
LUMINAL_MODEL=
```

Obtain the **documented OpenAI-compatible API base URL** and exact **chat model ID** from Luminal. Include the version path if required; do not enter the full `/chat/completions` endpoint because the SDK appends it. The sidebar now pre-fills the non-secret base URL and model confirmed in the user-supplied Luminal dashboard: `https://flash.luminal.cloud/v1` and `deepseek-ai/DeepSeek-V4.1-Flash`. They remain editable. HTTPS is required. You can also enter the values in the sidebar. Select **Luminal · live AI** before generating a plan or drafts.

Each click may consume credits. Requests time out after 25 seconds, and automatic retries are disabled. Live planning sends your event description and last-created volunteer roster (or the sample roster if none exists). Other live actions send relevant event details, shifts, names, assigned work and validated issues. Keys are never saved in event documents. Keep `.env` private. `.env` and `.env.*` are ignored by Git, except the key-free `.env.example`. Collapse Private AI settings during recordings.

Live responses are not trusted as scheduling facts: event-plan JSON is validated, and the coordinator approves it. Message and briefing accuracy still needs human review. A provider may return malformed JSON; the app rejects it and retains your existing event.

**Demo mode is explicitly local:** the event creator shows a fixed sample fixture and does not interpret the typed description. Other demo outputs are deterministic templates/checklists. This prevents claiming template output is live AI.

## Configure MongoDB Atlas
No MongoDB credential is necessary for the local demo. For Atlas:

1. Create a cluster and a database user with access to the `crewsync` database.
2. Add the app computer's IP to the Atlas access list.
3. In Atlas, choose **Connect → Drivers → Python** and copy the connection string.
4. Replace the placeholders with your database username/password. URL-encode special characters in credentials as required by the URI format.
5. Put it in your local `.env`, then restart the app:

```dotenv
MONGODB_URI=
MONGODB_DATABASE=crewsync
```

You can also enter the connection URI in the sidebar’s Database connection panel. Select **MongoDB Atlas** in the sidebar. Create an event, click **Save current event**, then reopen it. Check the `crewsync.events` collection in Atlas to demonstrate the integration. Saved snapshots include the event, volunteers, shifts, assignments, task status and announcement. One atomic document per event avoids partial saves across multiple collections. It updates the same event ID when you save again.

Atlas reads and writes have bounded timeouts. Failures leave the current event in the browser session and display the error category without exposing credentials. If no URI is configured, the app explicitly indicates it is using the local library. To intentionally save locally after an Atlas failure, select Local library and click Save.

Connection instructions reference the [official PyMongo Atlas guide](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/get-started/). A real Atlas connection must be verified with your configured credentials.

## Working with events
- **Start a new sample event** creates an independent event ID and seeds the editable setup.
- Click **Create my schedule →** after editing event details, volunteers or shifts. Existing event edits preserve its ID and checklist. Task owners are reconciled by unique name; ambiguous or removed names become Unassigned.
- AI drafts remain proposals until **Approve & create event**. Approval creates a new event, with a suggested announcement/checklist. Edit event details in the normal form if needed.
- The advanced proposal JSON editor lets you revise the entire AI proposal before approval.
- Use **Update checklist** to apply checklist edits. Changes do not contact volunteers.
- Use **Save current event** to persist changes. There is no autosave. An unsaved event can be lost when its browser session ends.
- **Use this roster for a new event** reuses saved volunteers in a new, independently saved event. Review the proposed sample shifts and event details.
- **Open selected event** restores the stored roster, schedule and checklist. Switching events discards unsaved changes in the current workspace; save first.
- Cancelled volunteers are removed from this event only. Review the preview, then approve to apply it. Save again to persist the change.
- Local data is in ignored `.data/` files. Set `CREWSYNC_DATA_DIR` to change the directory. The project download excludes saved records.

## Scheduling limits
Same-day shifts only, in the selected event time zone. `Maximum shifts` is an assignment-count limit, not an hours limit. Volunteers must be available for the entire shift. Adjacent shifts are allowed; overlapping assignments are not.

Roles are interchangeable. No employee compliance rules, skill constraints, breaks, payroll, budgets or multi-day events are modeled. Use this version for one-day volunteer events; weekly restaurant staffing is future scope.

The allocator is deterministic and greedy (scarce shifts first, then fewer assigned shifts). It never intentionally violates constraints but does not prove an optimal allocation. Some gaps may require manual rearrangement. Help-request candidates are individual suggestions; accepting several requests can create conflicts and needs a rebuilt/validated schedule.

Local storage and Atlas library access are for a trusted coordinator on this computer. There is no login or per-user database isolation. Do not expose the app publicly with real records until authentication and authorization are implemented.

## Test
```sh
python -m unittest discover -v
```

Tests cover scheduling, invalid inputs, proposal validation, unknown AI task owners, cancellation non-mutation, task-owner reconciliation, storage roundtrips and rejected unsafe IDs. Development also verified the complete Streamlit interaction flow and the AI/MongoDB request contracts with mock services. Live Luminal and Atlas are not confirmed without real configuration.

## Code map
- `app.py`: coordinator workspace.
- `workspace.py`: dashboard, planning approval, tasks and cancellation UI.
- `product.py`: proposal validation and safe action proposals.
- `storage.py`: local/MongoDB event snapshots.
- `coordinator.py`: allocation, conflict checks, exports and templates.
- `setup_ui.py`: user-facing table inputs.
- `ai_client.py`: configured chat API calls.
- `ui.py`: visual themes, motion and shift cards.

See `../TESTING.md` for Chicago/Mumbai scenario inputs, expected results and live checks. See `../DEMO.md` for a 90-second script and sponsor checklist. API references: [Streamlit](https://docs.streamlit.io/develop/api-reference), [official OpenAI Python client](https://github.com/openai/openai-python), [PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/).

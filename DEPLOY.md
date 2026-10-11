# Deploy CrewSync on Streamlit Community Cloud

1. Open https://share.streamlit.io and sign in with the GitHub account that owns `palashDoshi1/CrewSync`.
2. Create an app and choose deployment from GitHub.
3. Repository: `palashDoshi1/CrewSync`; branch: `main`; entry point: `app.py`.
4. Open Advanced settings, choose Python 3.12, and add this non-secret configuration:

```toml
CREWSYNC_PUBLIC_DEMO = "true"
```

5. Deploy and wait for the app to build. Copy its actual `.streamlit.app` URL once ready.
6. If judges need access, open the app sharing settings and select the appropriate app visibility. The source repository can remain private.
7. Test the deployed app: create a sample schedule, preview/approve a cancellation, complete a task, save/reopen in the same browser session, and play the video.

The deployed demo does not use MongoDB. Stored event snapshots belong to the visitor's current browser session. Local storage remains available when running on your own computer.

Do not put a Luminal key in GitHub or in README. Use the collapsed Private AI settings field for your live demonstration. The URL and model are prefilled. Collapse the sidebar during the recording. Public visitors can use demo mode without credentials.

Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

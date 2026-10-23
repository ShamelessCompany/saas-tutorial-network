"""YouTube Data API v3 uploader with OAuth2 token auto-refresh and resumable upload."""
import os
import time
import http.client
from pathlib import Path
from typing import List, Optional

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_authenticated_service(
    client_secrets_file: str | Path = "credentials/client_secret.json",
    token_file: str | Path = "credentials/token.json"
):
    """Authenticate via OAuth 2.0. Auto-refreshes token for headless 24/7 VPS operation."""
    if not GOOGLE_LIBS_AVAILABLE:
        raise ImportError(
            "Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib"
        )

    creds = None
    token_path = Path(token_file)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_UPLOAD_SCOPE)

    # Refresh or prompt flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_file), YOUTUBE_UPLOAD_SCOPE
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

def upload_to_youtube(
    video_path: str | Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    category_id: str = "28",  # 28: Science & Technology
    privacy_status: str = "public",  # "public", "private", "unlisted"
    client_secrets_file: str | Path = "credentials/client_secret.json",
    token_file: str | Path = "credentials/token.json",
    dry_run: bool = False
) -> str:
    """
    Uploads a video to YouTube with resumable chunks.
    If dry_run=True or credentials are missing, simulates upload and returns a mock ID.
    """
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")

    token_p = Path(token_file)
    if dry_run or not token_p.exists():
        print(f"[YouTube Uploader (Dry Run)] Simulating upload for: {path.name}")
        print(f"  -> Titulo: {title}")
        print(f"  -> Visibilidad: {privacy_status}")
        return "mock_yt_video_id_12345"

    youtube = get_authenticated_service(client_secrets_file, token_file)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["software", "tutorial", "automatizacion", "saas"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # 1MB chunk size for reliable resumable upload over VPS connections
    media = MediaFileUpload(str(path), chunksize=1024 * 1024, resumable=True)

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retries = 0
    max_retries = 5

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"[YouTube] Subiendo {int(status.progress() * 100)}%...")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retries < max_retries:
                retries += 1
                sleep_secs = 2 ** retries
                print(f"[YouTube] Error HTTP {e.resp.status}. Reintentando en {sleep_secs}s...")
                time.sleep(sleep_secs)
            else:
                raise

    video_id = response.get("id")
    print(f"[YouTube] Subida exitosa! Video ID: {video_id} -> https://youtu.be/{video_id}")
    return video_id

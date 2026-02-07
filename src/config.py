from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""

    # OpenAI
    openai_api_key: str

    # Apify
    apify_api_token: str = ""

    # YouTube
    youtube_api_key: str = ""

    # Resend
    resend_api_key: str

    # Email
    digest_recipient_email: str
    digest_from_email: str = "Learning Feed <digest@yourdomain.com>"

    # Feedback API
    feedback_api_url: str = "http://localhost:8000"

    # Sources (comma-separated)
    twitter_list_urls: str = ""
    twitter_handles: str = ""
    rss_feed_urls: str = ""
    youtube_channel_ids: str = ""

    # Streamlit
    streamlit_app_url: str = ""

    # Budget limits
    daily_budget_usd: float = 1.00
    monthly_budget_usd: float = 15.00

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def twitter_lists(self) -> list[str]:
        return [u.strip() for u in self.twitter_list_urls.split(",") if u.strip()]

    @property
    def twitter_handle_list(self) -> list[str]:
        return [h.strip().lstrip("@") for h in self.twitter_handles.split(",") if h.strip()]

    @property
    def rss_feeds(self) -> list[str]:
        return [u.strip() for u in self.rss_feed_urls.split(",") if u.strip()]

    @property
    def youtube_channels(self) -> list[str]:
        return [u.strip() for u in self.youtube_channel_ids.split(",") if u.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from .sources import Domain

# Each entry: (feed_url, source_name, domain)
RSS_FEEDS: list[tuple[str, str, Domain]] = [
    # AI/ML feeds
    (
        "https://huggingface.co/blog/feed.xml",
        "huggingface_blog",
        Domain.AI_ML,
    ),
    (
        "https://blog.langchain.dev/rss/",
        "langchain_blog",
        Domain.AI_ML,
    ),
    (
        "https://simonwillison.net/atom/everything/",
        "simon_willison",
        Domain.AI_ML,
    ),
    (
        "https://www.deeplearning.ai/the-batch/feed/",
        "deeplearning_ai_batch",
        Domain.AI_ML,
    ),
    (
        "https://openai.com/news/rss.xml",
        "openai_news",
        Domain.AI_ML,
    ),
    # Fintech feeds
    (
        "https://techcrunch.com/category/fintech/feed/",
        "techcrunch_fintech",
        Domain.FINTECH,
    ),
    (
        "https://www.finextra.com/rss/headlines.aspx",
        "finextra",
        Domain.FINTECH,
    ),
    (
        "https://www.pymnts.com/feed/",
        "pymnts",
        Domain.FINTECH,
    ),
]
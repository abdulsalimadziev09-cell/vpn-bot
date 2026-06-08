from app.services.extractor import build_search_text
from app.services.search import search_items
from app.services.tag_suggester import merge_tags


def test_build_search_text_for_tag_query() -> None:
    text = build_search_text(
        title="Kubernetes cheatsheet",
        body="Полезные команды kubectl",
        url="https://kubernetes.io/docs",
        transcription=None,
        tags=merge_tags(["devops"], ["kubernetes"]),
    )
    assert "kubernetes" in text.lower()
    assert "devops" in text


async def test_search_items_empty_query() -> None:
    class FakeSession:
        async def execute(self, *_args, **_kwargs):
            raise AssertionError("execute should not be called for empty query")

    items = await search_items(FakeSession(), user_id=1, query="   ")
    assert items == []

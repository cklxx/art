from alex_agent.apps.paper_review import (
    ImageBatchRequest,
    ImagePrompt,
    PaperAnalysisRequest,
    analyze_paper,
    generate_review_images,
)
from alex_agent.llm.google_client import GoogleGenerativeClient


def test_analyze_paper_builds_prompts():
    client = GoogleGenerativeClient(api_key=None, text_model="test-model", image_model="test-image")
    req = PaperAnalysisRequest(title="Test", abstract="A short abstract about models")
    result = analyze_paper(req, client)
    assert result.image_prompts
    assert len(result.key_points) >= 1


def test_generate_review_images_returns_placeholders():
    client = GoogleGenerativeClient(api_key=None, text_model="test-model", image_model="test-image")
    batch = ImageBatchRequest(prompts=[ImagePrompt(id="p1", prompt="chart of results")])
    result = generate_review_images(batch, client)
    assert result.images
    assert result.images[0].url.startswith("https://")

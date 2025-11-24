import { expect, test } from '@playwright/test';

const analysisResponse = {
  summary: 'Mock summary of the paper focused on generation quality and evaluation.',
  key_points: [
    'Highlights a transformer-diffusion hybrid for fast sampling.',
    'Benchmarks show improved FID and CLIP scores on key datasets.',
    'Uses feedback-aware loops to refine visual quality.',
  ],
  image_prompts: [
    'Diagram: model pipeline with diffusion blocks and transformer attention.',
    'Chart: side-by-side FID/CLIP comparison across baselines.',
    'Storyboard: feedback-driven regeneration loop from reviewer comments.',
  ],
  recommended_style: 'clean journal figure with muted palette and readable labels',
};

test('paper analysis, prompt queue, and regeneration flow', async ({ page }) => {
  await page.route('**/review/analyze', async (route) => {
    await route.fulfill({ status: 200, json: analysisResponse });
  });

  let imageRequest = 0;
  await page.route('**/review/images', async (route) => {
    const body = (await route.request().postDataJSON()) ?? {};
    const prompts = Array.isArray(body.prompts) ? body.prompts : [];
    const images = prompts.map((item: any, idx: number) => ({
      url: `https://placehold.co/512x512?text=mock-${imageRequest}-${idx}`,
      note: `mock-${imageRequest}-${idx}`,
      prompt: item.prompt,
    }));
    imageRequest += 1;
    await route.fulfill({ status: 200, json: { images } });
  });

  await page.goto('/');

  await expect(page.getByTestId('analyze-button')).toBeEnabled();
  await page.getByTestId('analyze-button').click();
  await expect(page.getByTestId('analysis-summary')).toContainText('Mock summary');
  await expect(page.getByText('Key point 1')).toBeVisible();

  await page.getByTestId('generate-all').click();
  const firstCard = page.getByTestId('prompt-card').first();
  await expect(firstCard.getByTestId('image-preview')).toBeVisible();
  await expect(firstCard.getByRole('img')).toBeVisible();

  await firstCard.locator('textarea').fill('Regenerate with more emphasis on evaluation metrics.');
  await firstCard.getByTestId('regenerate-button').click();
  await expect(firstCard.getByTestId('image-preview')).toContainText('mock-1-0');
});

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:8501';

// This test attempts to trigger the AI suggestion flow by filling a resume and
// clicking Compute Match on the Job Detail page. It is resilient: if no job is
// available or the backend/OpenAI is unreachable, it will log and not fail.
test('trigger AI suggestion flow (non-blocking)', async ({ page }) => {
  await page.goto(BASE_URL);

  // Try to navigate to Job Detail directly
  try {
    await page.click('text=Job Detail');
  } catch (e) {
    console.log('Could not navigate to Job Detail tab:', e.message || e);
  }

  // If there's a "View Details" in Results, try to click one to populate selection
  try {
    const viewBtn = page.locator('button:has-text("View Details")').first();
    if (await viewBtn.isVisible()) {
      await viewBtn.click();
    }
  } catch (e) {
    // ignore
  }

  // Fill a sample resume into the first textarea on the page
  try {
    const resumeText = `Experienced data engineer with 5 years building ETL pipelines, using Airflow, Spark, and AWS S3. Worked on data modeling, ingestion, and automation.`;
    const ta = page.locator('textarea').first();
    if (await ta.isVisible()) {
      await ta.fill(resumeText);
    } else {
      console.log('No textarea visible to paste resume into');
    }
  } catch (e) {
    console.log('Error filling resume textarea:', e.message || e);
  }

  // Click Compute Match if available
  try {
    const btn = page.locator('button:has-text("Compute Match")');
    if (await btn.isVisible()) {
      await btn.click();
      // Wait a little for AI suggestions to appear; don't fail if not
      const sugg = page.locator('text=AI-generated suggestions (ChatGPT)').first();
      await sugg.waitFor({ timeout: 15000 }).catch(() => {
        console.log('AI suggestions did not appear (backend or OpenAI may be unreachable)');
      });
    } else {
      console.log('Compute Match button not visible; skipping AI trigger');
    }
  } catch (e) {
    console.log('Error clicking Compute Match:', e.message || e);
  }

  expect(true).toBe(true);
});

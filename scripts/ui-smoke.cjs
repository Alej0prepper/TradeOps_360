'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const output = path.resolve('.ci/data/evidence');
const manifest = JSON.parse(fs.readFileSync(path.join(output, 'acceptance-manifest.json'), 'utf8'));
const password = process.env.TRADEOPS_DEMO_PASSWORD;
if (!password) throw new Error('A disposable demo password is required.');
const base = 'http://127.0.0.1:8069';

async function signIn(page, login) {
  await page.goto(`${base}/web/login?db=tradeops_ci`);
  await page.locator('input[name="login"]').fill(login);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await page.waitForURL(url => url.pathname === '/web', { timeout: 60000 });
  await page.locator('.o_main_navbar').waitFor({ state: 'visible', timeout: 60000 });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  let page;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await signIn(page, 'phase1_operator');
    const forms = [
      ['import', 'trade.import', manifest.import_id],
      ['presale', 'trade.presale', manifest.presale_id],
      ['sale', 'sale.order', manifest.sale_id],
      ['distribution', 'trade.distribution', manifest.distribution_id],
      ['incident', 'trade.delivery.incident', manifest.incident_id],
      ['reconciliation', 'trade.reconciliation', manifest.reconciliation_id],
    ];
    for (const [label, model, id] of forms) {
      await page.goto(`${base}/web#id=${id}&model=${model}&view_type=form`);
      await page.locator('.o_form_view').waitFor({ state: 'visible', timeout: 45000 });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.locator('.o_error_dialog').count(), 0, `Unexpected error in ${model}`);
      assert.ok((await page.locator('.o_form_view').innerText()).trim().length > 30);
      await page.screenshot({ path: path.join(output, `ui-${label}.png`), fullPage: true });
      results.push({ model, id, visible: true });
    }
    const response = await context.request.get(`${base}/report/pdf/trade_import.report_import_summary/${manifest.import_id}`);
    assert.equal(response.status(), 200, 'PDF report HTTP response');
    const pdf = await response.body();
    assert.equal(pdf.subarray(0, 4).toString(), '%PDF', 'Expected a PDF report');
    assert.ok(pdf.length > 1000, 'Expected a populated PDF');
    fs.writeFileSync(path.join(output, 'import-summary.pdf'), pdf);
    assert.deepEqual(errors, [], 'Browser application errors');
    await context.close();
    const viewerContext = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    page = await viewerContext.newPage();
    await signIn(page, 'phase1_viewer');
    await page.goto(`${base}/web#id=${manifest.import_id}&model=trade.import&view_type=form`);
    await page.locator('.o_form_view').waitFor({ state: 'visible', timeout: 45000 });
    assert.equal(await page.getByRole('button', { name: 'Validate / Create RFQ', exact: true }).count(), 0);
    await page.screenshot({ path: path.join(output, 'ui-consultation.png'), fullPage: true });
    await viewerContext.close();
    const result = { verified: true, forms: results, consultation_read: true,
                     pdf_bytes: pdf.length, browser: browser.version() };
    fs.writeFileSync(path.join(output, 'ui-smoke.json'), JSON.stringify(result, null, 2) + '\n');
    console.log('TRADEOPS_UI_SMOKE_VERIFIED', JSON.stringify(result));
  } catch (error) {
    if (page && !page.isClosed()) await page.screenshot({ path: path.join(output, 'ui-failure.png'), fullPage: true }).catch(() => {});
    throw error;
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

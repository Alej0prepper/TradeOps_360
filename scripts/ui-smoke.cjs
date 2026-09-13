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
const normalize = value => value.trim().replace(/\s+/g, ' ');

async function signIn(page, login) {
  await page.goto(`${base}/web/login?db=tradeops_ci`);
  await page.locator('input[name="login"]').fill(login);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await page.waitForURL(url => url.pathname === '/web', { timeout: 60000 });
  await page.locator('.o_main_navbar').waitFor({ state: 'visible', timeout: 60000 });
}

async function expectedValue(context, model, id, field) {
  // Read as the signed-in normal user; do not bypass ACLs to obtain expectations.
  const response = await context.request.post(`${base}/web/dataset/call_kw/${model}/read`, {
    data: { jsonrpc: '2.0', method: 'call', id: 1,
            params: { model, method: 'read', args: [[id], [field]], kwargs: {} } },
  });
  assert.equal(response.status(), 200, `Read ${model} ${id}`);
  const data = await response.json();
  assert.ok(!data.error, `Cannot read expected record: ${JSON.stringify(data.error)}`);
  assert.equal(data.result.length, 1, 'One existing record is required');
  assert.equal(data.result[0].id, id);
  const value = data.result[0][field];
  assert.ok(typeof value === 'string' && normalize(value).length > 0, 'Record identity must not be empty');
  return normalize(value);
}

async function waitForRecord(page, field, expected) {
  const selector = `.o_form_view .o_field_widget[name="${field}"]`;
  await page.locator(selector).waitFor({ state: 'visible', timeout: 45000 });
  await page.waitForFunction(({ selector, expected }) => {
    const widget = document.querySelector(selector);
    if (!widget || !widget.getClientRects().length) return false;
    const input = widget.querySelector('input, textarea');
    const value = input ? input.value : widget.innerText;
    return value.trim().replace(/\s+/g, ' ') === expected;
  }, { selector, expected }, { timeout: 45000 });
  await page.evaluate(() => document.fonts.ready);
  const observed = await page.locator(selector).evaluate(widget => {
    const input = widget.querySelector('input, textarea');
    return input ? input.value : widget.innerText;
  });
  assert.equal(normalize(observed), expected);
  assert.equal(await page.locator('.o_error_dialog').count(), 0);
  return normalize(observed);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  const errors = [];
  let page;
  const trackedPage = async context => {
    const result = await context.newPage();
    result.on('pageerror', error => errors.push(error.message));
    return result;
  };
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    page = await trackedPage(context);
    await signIn(page, 'phase1_operator');
    await page.close();
    const forms = [
      ['import', 'trade.import', manifest.import_id, 'name'],
      ['presale', 'trade.presale', manifest.presale_id, 'name'],
      ['sale', 'sale.order', manifest.sale_id, 'name'],
      ['distribution', 'trade.distribution', manifest.distribution_id, 'name'],
      ['incident', 'trade.delivery.incident', manifest.incident_id, 'description'],
      ['reconciliation', 'trade.reconciliation', manifest.reconciliation_id, 'name'],
    ];
    for (const [label, model, id, field] of forms) {
      const expected = await expectedValue(context, model, id, field);
      // A fresh document cannot accidentally satisfy assertions on the previous
      // form while Odoo's hash router is still replacing its action component.
      page = await trackedPage(context);
      await page.goto(`${base}/web#id=${id}&model=${model}&view_type=form`);
      const observed = await waitForRecord(page, field, expected);
      await page.screenshot({ path: path.join(output, `ui-${label}.png`), fullPage: true, animations: 'disabled' });
      await waitForRecord(page, field, expected);
      results.push({ model, id, visible: true, fresh_page: true, record_identity_verified: true,
                     checked_field: field, expected_value: expected, observed_value: observed });
      await page.close();
    }
    const response = await context.request.get(`${base}/report/pdf/trade_import.report_import_summary/${manifest.import_id}`);
    assert.equal(response.status(), 200, 'PDF report HTTP response');
    const pdf = await response.body();
    assert.equal(pdf.subarray(0, 4).toString(), '%PDF', 'Expected a PDF report');
    assert.ok(pdf.length > 1000, 'Expected a populated PDF');
    fs.writeFileSync(path.join(output, 'import-summary.pdf'), pdf);
    await context.close();
    const viewerContext = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    page = await trackedPage(viewerContext);
    await signIn(page, 'phase1_viewer');
    await page.close();
    const viewerExpected = await expectedValue(viewerContext, 'trade.import', manifest.import_id, 'name');
    assert.equal(viewerExpected, manifest.import_name);
    page = await trackedPage(viewerContext);
    await page.goto(`${base}/web#id=${manifest.import_id}&model=trade.import&view_type=form`);
    await waitForRecord(page, 'name', viewerExpected);
    // Refresh is visible to an operator even on a completed import; its absence
    // therefore tests the consultation role rather than only a state condition.
    assert.equal(await page.locator('button[name="action_refresh_receipts"]').count(), 0);
    assert.equal(await page.getByRole('button', { name: 'Validate / Create RFQ', exact: true }).count(), 0);
    await page.screenshot({ path: path.join(output, 'ui-consultation.png'), fullPage: true, animations: 'disabled' });
    await viewerContext.close();
    assert.deepEqual(errors, [], 'Browser application errors');
    const result = { verified: true, forms: results, consultation_read: true,
                     consultation_identity_verified: true, pdf_bytes: pdf.length, browser: browser.version() };
    fs.writeFileSync(path.join(output, 'ui-smoke.json'), JSON.stringify(result, null, 2) + '\n');
    console.log('TRADEOPS_UI_SMOKE_VERIFIED', JSON.stringify(result));
  } catch (error) {
    if (page && !page.isClosed()) await page.screenshot({ path: path.join(output, 'ui-failure.png'), fullPage: true }).catch(() => {});
    throw error;
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

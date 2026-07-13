const fs = require('fs');
const path = require('path');
const assert = require('assert');
const source = fs.readFileSync(path.join(__dirname, '..', 'wordpress-plugin', 'sustainable-catalyst-workbench', 'assets', 'js', 'sc-workbench-v302.js'), 'utf8');
for (const marker of ['sc-workbench-migration-plan/2.0','sc-workbench-backup/2.0','sc-workbench-restore-plan/2.0','CLEAN WORKSPACE','ROLLBACK WORKBENCH','MutationObserver','crypto.subtle','localStorage']) assert(source.includes(marker), `Missing marker: ${marker}`);
const router = fs.readFileSync(path.join(__dirname, '..', 'wordpress-plugin', 'sustainable-catalyst-workbench', 'assets', 'js', 'scwb-primary-repair.js'), 'utf8');
assert(router.includes("'recovery'"));
assert(router.includes("version: '3.1.0'"));
console.log('Workbench v3.1.0 browser recovery source audit passed.');

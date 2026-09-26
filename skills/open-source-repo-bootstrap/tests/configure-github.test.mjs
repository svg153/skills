import test from 'node:test';
import assert from 'node:assert/strict';
import { makePlan, validateConfig } from '../scripts/configure-github.mjs';

const config = {
  repository: 'svg153/example',
  description: 'A community project.',
  homepage: 'https://github.com/svg153/example',
  topics: ['open-source', 'developer-tools'],
};

test('accepts repo-specific metadata but fixes the governance policy', () => {
  const plan = makePlan(config, { id: 42, login: 'maintainer' });

  assert.equal(plan.repository, config.repository);
  assert.deepEqual(plan.topics, config.topics);
  assert.equal(plan.metadata.allow_squash_merge, true);
  assert.equal(plan.metadata.allow_merge_commit, false);
  assert.equal(plan.metadata.allow_rebase_merge, false);
  assert.equal(plan.metadata.has_discussions, true);
  assert.equal(plan.ruleset.name, 'main-pull-request');
  assert.equal(plan.ruleset.bypass_actors[0].actor_id, 42);
  assert.deepEqual(
    plan.ruleset.rules.find((rule) => rule.type === 'required_status_checks').parameters.required_status_checks.map((check) => check.context),
    ['test', 'title', 'commits'],
  );
  assert.ok(plan.labels.some((label) => label.name === 'type:bug'));
});

test('limits bypass to the authenticated maintainer on every repo type', () => {
  const plan = makePlan(config, { id: 73, login: 'maintainer' });
  assert.deepEqual(plan.ruleset.bypass_actors, [
    { actor_id: 73, actor_type: 'User', bypass_mode: 'always' },
  ]);
});

test('rejects invalid repository metadata before invoking gh', () => {
  assert.throws(() => validateConfig({ ...config, repository: '../other/repo' }), /owner\/repo/);
  assert.throws(() => validateConfig({ ...config, homepage: 'javascript:alert(1)' }), /HTTPS/);
  assert.throws(() => validateConfig({ ...config, topics: ['duplicate', 'duplicate'] }), /duplicate/);
  assert.throws(() => validateConfig({ ...config, allow_merge_commit: true }), /Unsupported config field/);
});

#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const RULESET_NAME = 'main-pull-request';
const ACTIONS_INTEGRATION_ID = 15368;

export const LABELS = [
  { name: 'type:feature', color: '1d76db', description: 'User-visible feature' },
  { name: 'type:bug', color: 'd73a4a', description: 'Defect or regression' },
  { name: 'type:docs', color: '0075ca', description: 'Documentation' },
  { name: 'type:chore', color: '6f42c1', description: 'Maintenance or tooling' },
  { name: 'area:docs', color: 'cfd3d7', description: 'Documentation and assets' },
  { name: 'area:governance', color: '5319e7', description: 'Repository policy and contributor workflow' },
  { name: 'area:release', color: '0052cc', description: 'Release automation' },
  { name: 'area:tests', color: '0e8a16', description: 'Tests and validation' },
  { name: 'priority:p1', color: 'b60205', description: 'Highest priority' },
  { name: 'priority:p2', color: 'd93f0b', description: 'Normal priority' },
  { name: 'priority:p3', color: '0e8a16', description: 'Nice to have' },
];

const REPOSITORY_SETTINGS = {
  allow_squash_merge: true,
  allow_merge_commit: false,
  allow_rebase_merge: false,
  squash_merge_commit_title: 'PR_TITLE',
  squash_merge_commit_message: 'PR_BODY',
  delete_branch_on_merge: true,
  allow_auto_merge: true,
  has_issues: true,
  has_discussions: true,
  has_wiki: false,
};

export function validateConfig(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Config must be a JSON object.');
  }
  const allowed = ['repository', 'description', 'homepage', 'topics'];
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unknown.length) throw new Error(`Unsupported config field(s): ${unknown.join(', ')}.`);
  if (typeof value.repository !== 'string' || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(value.repository)) {
    throw new Error('repository must be a GitHub owner/repo slug.');
  }
  if (value.repository.split('/').some((part) => part === '.' || part === '..')) {
    throw new Error('repository must be a GitHub owner/repo slug.');
  }
  if (typeof value.description !== 'string' || !value.description.trim() || value.description.length > 350) {
    throw new Error('description must contain 1–350 characters.');
  }
  let homepage;
  try {
    homepage = new URL(value.homepage);
  } catch {
    throw new Error('homepage must be an HTTPS URL.');
  }
  if (homepage.protocol !== 'https:') throw new Error('homepage must be an HTTPS URL.');
  if (!Array.isArray(value.topics) || value.topics.length > 20 || value.topics.some((topic) =>
    typeof topic !== 'string' || !/^[a-z0-9][a-z0-9-]{0,49}$/.test(topic))) {
    throw new Error('topics must be an array of up to 20 lowercase GitHub topic slugs.');
  }
  if (new Set(value.topics).size !== value.topics.length) throw new Error('topics cannot contain duplicates.');

  return {
    repository: value.repository,
    description: value.description.trim(),
    homepage: homepage.toString().replace(/\/$/, ''),
    topics: [...value.topics],
  };
}

function makeRuleset(actor) {
  if (!actor || !Number.isInteger(actor.id)) {
    throw new Error('GitHub returned an unsupported authenticated user.');
  }

  return {
    name: RULESET_NAME,
    target: 'branch',
    enforcement: 'active',
    conditions: { ref_name: { include: ['refs/heads/main'], exclude: [] } },
    rules: [
      { type: 'deletion' },
      { type: 'non_fast_forward' },
      { type: 'required_linear_history' },
      {
        type: 'pull_request',
        parameters: {
          dismiss_stale_reviews_on_push: true,
          require_code_owner_review: true,
          require_last_push_approval: false,
          required_approving_review_count: 1,
          required_review_thread_resolution: true,
          allowed_merge_methods: ['squash'],
        },
      },
      {
        type: 'required_status_checks',
        parameters: {
          strict_required_status_checks_policy: true,
          do_not_enforce_on_create: false,
          required_status_checks: ['test', 'title', 'commits'].map((context) => ({
            context,
            integration_id: ACTIONS_INTEGRATION_ID,
          })),
        },
      },
    ],
    bypass_actors: [{ actor_id: actor.id, actor_type: 'User', bypass_mode: 'always' }],
  };
}

export function makePlan(configInput, actor) {
  const config = validateConfig(configInput);
  return {
    repository: config.repository,
    metadata: {
      description: config.description,
      homepage: config.homepage,
      ...REPOSITORY_SETTINGS,
    },
    topics: config.topics,
    privateVulnerabilityReporting: true,
    labels: LABELS,
    ruleset: makeRuleset(actor),
  };
}

function gh(args, input) {
  const result = spawnSync('gh', args, { encoding: 'utf8', input, shell: false });
  if (result.error) {
    if (result.error.code === 'ENOENT') throw new Error('GitHub CLI (gh) is required; install it and run `gh auth login`.');
    throw result.error;
  }
  if (result.status !== 0) throw new Error((result.stderr || result.stdout || 'gh command failed').trim());
  return result.stdout.trim();
}

function ghJson(args) {
  const output = gh(args);
  try {
    return JSON.parse(output);
  } catch {
    throw new Error(`Expected JSON from gh ${args.join(' ')}.`);
  }
}

function api(method, endpoint, body) {
  const args = ['api', '--method', method, endpoint];
  if (body !== undefined) args.push('--input', '-');
  return gh(args, body === undefined ? undefined : JSON.stringify(body));
}

function repoApi(repository, suffix = '') {
  return `repos/${repository}${suffix}`;
}

function inspectTarget(repository) {
  const target = ghJson(['api', repoApi(repository)]);
  if (target.private || target.visibility !== 'public') throw new Error(`${repository} must already be public.`);
  if (target.permissions?.admin !== true) throw new Error(`The authenticated gh account needs admin access to ${repository}.`);
  if (target.default_branch !== 'main') throw new Error(`${repository} must use main as its default branch before applying the standard ruleset.`);
  if (target.owner?.login?.toLowerCase() !== repository.split('/')[0].toLowerCase()) {
    throw new Error('The repository owner returned by GitHub does not match the config.');
  }
  return ghJson(['api', 'user']);
}

function existingRulesetId(repository) {
  const output = gh([
    'api', '--paginate', repoApi(repository, '/rulesets?per_page=100'),
    '--jq', `.[] | select(.name == "${RULESET_NAME}") | .id`,
  ]);
  const ids = output.split(/\r?\n/).filter(Boolean);
  if (ids.length > 1) throw new Error(`More than one ruleset is named ${RULESET_NAME}; remove the duplicate manually first.`);
  return ids[0];
}

function applyPlan(config) {
  gh(['auth', 'status']);
  const actor = inspectTarget(config.repository);
  const plan = makePlan(config, actor);
  const base = repoApi(config.repository);
  const rulesetId = existingRulesetId(config.repository);

  api('PATCH', base, plan.metadata);
  api('PUT', `${base}/topics`, { names: plan.topics });
  api('PUT', `${base}/private-vulnerability-reporting`);
  for (const label of plan.labels) {
    gh(['label', 'create', label.name, '--repo', config.repository, '--color', label.color, '--description', label.description, '--force']);
  }
  api(rulesetId ? 'PUT' : 'POST', rulesetId ? `${base}/rulesets/${rulesetId}` : `${base}/rulesets`, plan.ruleset);
  console.log(`Applied the complete standard policy to ${config.repository}. Re-run safely if an operation was interrupted.`);
}

function usage() {
  console.log('Usage: node configure-github.mjs --config <json-file> [--plan|--apply]');
}

async function main(args) {
  let configPath;
  let mode;
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--config' && !configPath && args[i + 1]) {
      configPath = args[++i];
    } else if ((args[i] === '--plan' || args[i] === '--apply') && !mode) {
      mode = args[i];
    } else {
      usage();
      process.exitCode = 2;
      return;
    }
  }
  if (!configPath) {
    usage();
    process.exitCode = 2;
    return;
  }
  const config = validateConfig(JSON.parse(await readFile(resolve(configPath), 'utf8')));
  mode ??= '--plan';

  if (mode === '--plan') {
    gh(['auth', 'status']);
    const actor = inspectTarget(config.repository);
    const plan = makePlan(config, actor);
    console.log(JSON.stringify({ mode: 'read-only plan; no GitHub changes', ...plan }, null, 2));
    return;
  }

  console.log(`Applying the full policy to ${config.repository}; reruns are idempotent and resources are never deleted.`);
  applyPlan(config);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main(process.argv.slice(2)).catch((error) => {
    console.error(`Repository bootstrap failed: ${error.message}`);
    process.exitCode = 1;
  });
}

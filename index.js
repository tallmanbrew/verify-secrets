const core = require('@actions/core');
const verify_secrets = require('./verify-secrets');

async function run() {
  try {
    const secretsJson = core.getInput('secrets');
    const secretNamesJson = core.getInput('secret_names');

    await verify_secrets(secretsJson, secretNamesJson);
  }
  catch (error) {
    core.setFailed(error.message);
  }
}

run()
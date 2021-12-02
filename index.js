const core = require('@actions/core');
const verify_secrets = require('./verify-secrets');

async function run() {
  try {

    const secretsJson = core.getInput('secrets');
    const secretNamesJson = core.getInput('secret_names');
    const exclusions = core.getInput('exclusions');

    await verify_secrets(secretsJson, secretNamesJson, exclusions);
  }
  catch (error) {
    core.setFailed(error.message);
  }
}

run()
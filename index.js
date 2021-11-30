const core = require('@actions/core');
const verify_secrets = require('./verify-secrets');

async function run() {
  try {
    const secrets = core.getInput('secrets');
    const secretNames = core.getInput('secret_names');

    await verify_secrets(secrets, secretNames);
  }
  catch (error) {
    core.setFailed(error.message);
  }
}

run()
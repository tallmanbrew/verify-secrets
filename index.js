const core = require('@actions/core');
const verify_secrets = require('./verify-secrets');

async function run() {
  try {
    const secrets = core.getInput('secrets');

    await verify_secrets(secrets);
  }
  catch (error) {
    core.setFailed(error.message);
  }
}

run()
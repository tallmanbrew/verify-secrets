const core = require('@actions/core');

async function run() {
  try {
    const secrets = core.getInput('secrets');
    const parsedSecrets = JSON.parse(secrets);

    let secretNames = []
    for(var attributeName in parsedSecrets){
      core.info(`Secret ${attributeName}`)
      secretNames.push(attributeName);
    }

    //let referencedSecretNames = []

  }
  catch (error) {
    core.setFailed(error.message);
  }
}

run()

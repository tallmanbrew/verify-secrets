const core = require('@actions/core');
const fs = require('fs');

let verify_secrets = async function (secrets) {

  const parsedSecrets = JSON.parse(secrets);

  core.info('Secrets available\n------------------------')

  let secretNames = new Set()
  for (var attributeName in parsedSecrets) {
    core.info(attributeName)
    secretNames.add(attributeName);
  }

  let referencedSecretNames = new Set()

  const workflowFiles = await fs.promises.readdir(".github/workflows");

  for (const workflowFile of workflowFiles) {
    workflowFileBuffer = await fs.promises.readFile(`.github/workflows/${workflowFile}`);
    workflowFileContent = workflowFileBuffer.toString();

    const secretRegex = /\{\{\s*secrets\.(.*?)\s*\}/g;
    let matches = [...workflowFileContent.matchAll(secretRegex)];

    for (const match of matches) {
      referencedSecretNames.add(match[1]);
    }
  }

  core.info('\nSecrets referenced in workflows\n------------------------')

  for (const referencedSecretName of Array.from(referencedSecretNames).sort()) {
    core.info(referencedSecretName);
  }

  let missingSecretNames = new Set([...referencedSecretNames].filter(x => !secretNames.has(x)));

  if (missingSecretNames.size > 0) {
    core.info('\n!!! MISSING SECRETS !!\n------------------------');

    for (const missingSecretName of Array.from(missingSecretNames).sort()) {
      core.info(missingSecretName);
    }

    core.setFailed();
  }
};

module.exports = verify_secrets;
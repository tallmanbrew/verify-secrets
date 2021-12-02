const core = require('@actions/core');
const fs = require('fs');

secrets = async function (secretsJson, secretNamesJson, exclusions) {

  const parsedSecrets = JSON.parse(secrets);

  let secretNames = new Set()

  for (var attributeName in parsedSecrets) {
    secretNames.add(attributeName);
  }

  core.info('Secrets available\n------------------------')
  
  for (const secretName of Array.from(secretNames).sort()) {
    core.info(secretName);
  }

  core.info('')

  let referencedSecretNames = new Set()

  const workflowFiles = await fs.promises.readdir(".github/workflows");

  for (const workflowFile of workflowFiles) {
    workflowFileBuffer = await fs.promises.readFile(`.github/workflows/${workflowFile}`);
    workflowFileContent = workflowFileBuffer.toString();

    const isReusableWorkflowRegex = /\:\s+workflow_call\:/g

    // Reusable workflows only use secrets passed to them so skip
    // parsing these files
    if (workflowFileContent.match(isReusableWorkflowRegex)) {
      core.info(`Skipping reusable workflow ${workflowFile}`)  
    }
    else{
      const secretRegex = /\{\{\s*secrets\.(.*?)\s*\}/g;
      let matches = [...workflowFileContent.matchAll(secretRegex)];
  
      for (const match of matches) {
        referencedSecretNames.add(match[1]);
      }
    }
  }

  core.info('\nSecrets referenced in workflows\n------------------------')
  
  for (const referencedSecretName of Array.from(referencedSecretNames).sort()) {
    core.info(referencedSecretName);
  }

  exclusion_secret_names = new Set()

  if (exclusions) {
    
    core.info('\nSecrets excluded from verification\n------------------------')
    
    exclusion_items = exclusions.split(',');

    for(const exclusion_item of exclusion_items){
      core.info(exclusion_item);
      exclusion_secret_names.add()
    }
  }

  let missingSecretNames = new Set([...referencedSecretNames].filter(x => !secretNames.has(x)));

  if (missingSecretNames.size > 0) {
    core.info('')

    for (const missingSecretName of Array.from(missingSecretNames).sort()) {
      if(!exclusion_secret_names.has(missingSecretName)){
        core.error(`Secret "${missingSecretName}" is not defined`);
      }
    }

    core.setFailed();
  }
};

module.exports = verify_secrets;
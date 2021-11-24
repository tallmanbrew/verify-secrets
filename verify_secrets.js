const core = require('@actions/core');
const fs = require('fs');

let verify_secrets = function (secrets) {
   
    const parsedSecrets = JSON.parse(secrets);
    core.info(parsedSecrets);
    
    let secretNames = []
    for(var attributeName in parsedSecrets){
      core.info(`Secret ${attributeName}`)
      secretNames.push(attributeName);
    }

    let referencedSecretNames = new Set()

    const workflowFiles = await fs.promises.readdir( ".github/workflows" );

    for(const workflowFile of workflowFiles){
      workflowFileBuffer = await fs.promises.readFile(`.github/workflows/${workflowFile}`);
      workflowFileContent = workflowFileBuffer.toString();

      const secretRegex = /\{\{\s*secrets\.(.*?)\s*\}/g;
      let matches = [...workflowFileContent.matchAll(secretRegex)];

      for(const match of matches){
        referencedSecretNames.add(match[1]);
      }

      core.info(workflowFileContent);
    }
};

module.exports = verify_secrets;
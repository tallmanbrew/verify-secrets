#!/bin/bash
gh auth login --with-token < token.txt

needs_exit="false"

github_secrets=$(gh secret list --repo $REPO)
github_secrets+=$(gh secret list -o $OWNER)
github_secrets=(${github_secrets[0]})  
yaml_secrets=$(grep -w "secrets.*" .github/workflows/*.yml | sed s'/.*{{\(.*\)}}/\1/')
yaml_secrets+=$(grep -w "secrets.*" .github/workflows/*.yaml | sed s'/.*{{\(.*\)}}/\1/')

for yaml_secret in $yaml_secrets;
do     
    if [[ "$yaml_secret" =~ "secrets"* ]]; 
    then
        if [[ ! "$yaml_secret" =~ "GITHUB_TOKEN" && ! "$yaml_secret" =~ "matrix" ]];
        then
            secret=(${yaml_secret//./ })
            if [[ ! " ${github_secrets[@]} " =~ " ${secret[1]} " ]]; 
            then
                echo ${secret[1]}
                needs_exit="true"
            fi
        fi
    fi
done

if [ "${needs_exit}" = "true" ];
then
    echo "Secrets listed above not setup in GitHub secrets store!"
    exit 1
fi

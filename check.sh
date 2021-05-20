#!/usr/bin/env bash
needs_exit="false"

github_repo_secrets=$(curl -H "Accept: application/vnd.github.v3+json" -u svcghc:$TOKEN https://api.github.com/repos/${REPO}/actions/secrets?per_page=100 | jq '.')
repo_secrets_json=$(jq '.secrets | .[].name' <<< "$github_repo_secrets")
repo_secrets_list=$(sed -e 's/^"//' -e 's/"$//' <<< "$repo_secrets_json")
if [ ! -z "${OWNER}" ];
then
    github_org_secrets=$(curl -H "Accept: application/vnd.github.v3+json" -u svcghc:$TOKEN https://api.github.com/orgs/${OWNER}/actions/secrets?per_page=100 | jq '.')
    org_secrets_json=$(jq '.secrets | .[].name' <<< "$github_org_secrets")
    org_secrets_list=$(sed -e 's/^"//' -e 's/"$//' <<< "$org_secrets_json")
fi

yaml_secrets=$(grep -w "{{ secrets.* }}" .github/workflows/*.yaml | sed s'/.*{{\(.*\)}}/\1/')
yml_secrets=$(grep -w "{{ secrets.* }}" .github/workflows/*.yml | sed s'/.*{{\(.*\)}}/\1/')

all_yaml_secrets=(${yaml_secrets[@]} ${yml_secrets[@]})

for yaml_secret in ${all_yaml_secrets[@]};
do     
    if [[ "${yaml_secret}" =~ "secrets"* ]]; 
    then
        if [[ ! "${yaml_secret}" =~ "GITHUB_TOKEN" && ! "${yaml_secret}" =~ "matrix" ]];
        then
            secret=(${yaml_secret//./ });
            if [[ ! " ${repo_secrets_list[@]} " =~ " ${secret[1]} " ]]; 
            then
                echo ${secret[1]};
                needs_exit="true";
            fi
        fi
    fi
done

if [ "${needs_exit}" = "true" ];
then
    echo "Secrets listed above not setup in GitHub secrets store!"
    exit 1
fi

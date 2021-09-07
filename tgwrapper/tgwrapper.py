#!/usr/bin/env python3

import os
import sys
import copy
import yaml
import dpath
import shutil
import logging
from dpath import util
from collections import defaultdict
from mergedeep import merge, Strategy
from tgwrapper.tghelper import tghelper
from jinja2 import Environment, FileSystemLoader, exceptions


def find_project_dir():
    """
     Find the root of the project
    :return: Project root directory
    """
    # Depending on the location of current script, change the path
    # project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if "PROJECT_ROOT" in os.environ:
        project_root_dir = os.getenv("PROJECT_ROOT")
    else:
        project_root_dir = os.getcwd()

    return project_root_dir.rstrip("/")


def is_path_exist(*args):
    """
    :param args:  List of files and dictionaries
    :return: Validate if the path exist
    """
    for path in args:
        if not os.path.exists(path):
            logging.error(f"{path} not found")
            sys.exit(1)


def delete_tg_cache(list_of_dirs):
    """
    :param list_of_dirs:  List of directories to be deleted
    :return: None
    """
    for dir_to_delete in list_of_dirs:
        shutil.rmtree(os.getcwd() + '/' + dir_to_delete, ignore_errors=True)


def get_terragrunt_modules_list():
    """
    Starting from the directory where the script is executed,
    it returns a list of terragrunt_modules directory
    :return:
    """
    active_modules = list()
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file == 'terragrunt.hcl' and '.terragrunt-cache' not in root:
                active_modules.append(os.path.join(root, file))
    return active_modules


def nested_dict():
    """
    Creates a default dictionary where each value is an other default dictionary.
    """
    return defaultdict(nested_dict)


def default_to_regular(d):
    """
    Converts defaultdicts of defaultdicts to dict of dicts.
    """
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d


def get_path_dict(paths, terragrunt_module_abs_path):
    new_path_dict = nested_dict()
    for path in paths:
        full_path = copy.deepcopy(path)
        full_path = full_path.replace('terragrunt.hcl', '')
        parts = list()
        if 'terragrunt_modules/terragrunt.hcl' not in path:
            path = path.replace('terragrunt.hcl', 'path')
            path = path.split(terragrunt_module_abs_path)[1]
            parts = path.split('/')
        if parts:
            marcher = new_path_dict
            for key in parts[:-1]:
                marcher = marcher[key]
            marcher[parts[-1]] = parts[-1]
            marcher['path'] = full_path

    return default_to_regular(new_path_dict)


def afilter(x):
    """
    Returns True only for those modules eligible to be deployed against a given environment and region
    :param x:
    :return:
    """

    if isinstance(x, dict):
        if 'allowed_envs' and 'allowed_regions' in x.keys():
            if env in x['allowed_envs'] and region in x['allowed_regions']:
                return True
    return False


def get_eligible_modules(current_dict):
    """
    :param current_dict:
    :return: Return the list of directories where the terragrunt apply will be executed
    """
    result = dpath.util.search(current_dict['terragrunt_modules_settings'], '**', afilter=afilter)
    return result


def write_config_file(env_override_file, config_template, env, region):
    """
    :param env_override_file:
    :param config_template: Common template file
    :param env: Environment name
    :param region: AWS Region
    :return: Config dict for terragrunt
    """

    try:
        j2_env = Environment(extensions={'jinja2_ansible_filters.AnsibleCoreFiltersExtension'},
                             loader=FileSystemLoader(os.path.dirname(config_template)),
                             trim_blocks=True, lstrip_blocks=True, autoescape=True)
        template = j2_env.get_template(os.path.basename(env_override_file))
        env_override_rendered = template.render(AWS_REGION=region)
    except exceptions.UndefinedError as e:
        raise SystemExit(e)

    logging.debug(f"Rendered environment override file - {env_override_rendered}")

    try:

        env_override_dict = yaml.safe_load(env_override_rendered)
        regional_override_dict = env_override_dict['env_settings']['regions'][region]
        merge(env_override_dict["env_settings"]["terragrunt_modules_settings"], regional_override_dict,
              regional_override_dict, strategy=Strategy.REPLACE)
        env_override_dict['AWS_REGION'] = region
        env_override_dict['AWS_ENV'] = env
        merged_regional_override_dict = env_override_dict['env_settings']['terragrunt_modules_settings']
        conf_dict = yaml.safe_load(open(config_template))
        merge(conf_dict['terragrunt_modules_settings'], merged_regional_override_dict)
    except Exception as e:
        raise SystemExit(e)

    logging.debug(f"Merged regional override dict - {merged_regional_override_dict}")
    logging.debug(f"Final config file - {yaml.dump(conf_dict)}")

    # Write conf to file
    try:
        with open(f"{os.path.dirname(config_template)}/template_{env}_{region}.yml", 'w') as p:
            yaml.dump(conf_dict, p, default_flow_style=False)
    except IOError as e:
        raise SystemExit(e)

    return conf_dict


def run_terragrunt(action, config_dir, config_template, env,
                   profile, region, terraform_args, tg_mod_dir) -> None:
    """
    :param action:
    :param config_dir:
    :param config_template:
    :param env:
    :param profile:
    :param region:
    :param terraform_args:
    :param tg_mod_dir:
    :return:
    """
    project_root = find_project_dir()
    logging.info(f"PROJECT_ROOT is set to - {project_root}")
    delete_tg_cache([".terragrunt-cache"])

    # Arguments mock
    env_conf_file_path = f"{project_root}/{config_dir}/{env}_override.yml"
    conf_template_path = f"{project_root}/{config_dir}/{config_template}"
    terragrunt_modules_path = f"{project_root}/{tg_mod_dir}/"
    terragrunt_ignore_dirs = list()

    is_path_exist(env_conf_file_path, terragrunt_modules_path, conf_template_path)

    # Write the conf to file and get a dict back
    config_file = write_config_file(env_conf_file_path, conf_template_path, env, region)

    # Remove the cache folder
    active_modules_list = get_terragrunt_modules_list()
    logging.debug(f"List of active modules - {active_modules_list}")

    path_dict = get_path_dict(active_modules_list, terragrunt_modules_path)
    logging.debug(f"Terragrunt module settings - {config_file['terragrunt_modules_settings']}")

    dpath.util.merge(config_file['terragrunt_modules_settings'], path_dict)
    logging.debug(f"Merged config file - {config_file}")

    # Removed Path
    eligible_terragrunt_modules_dict = get_eligible_modules(config_file)
    logging.debug(f"Eligible terragrunt module dict - {eligible_terragrunt_modules_dict}")

    total_terragrunt_modules_list = dpath.util.values(config_file['terragrunt_modules_settings'], '**/path')
    logging.debug(f"All terragrunt module list - {total_terragrunt_modules_list}")

    eligible_terragrunt_modules_list = dpath.util.values(eligible_terragrunt_modules_dict, '**/path')
    logging.debug(f"Eligible terragrunt module list - {eligible_terragrunt_modules_list}")

    excluded_terragrunt_modules_list = set(total_terragrunt_modules_list) - set(eligible_terragrunt_modules_list)
    logging.debug(f"Excluded terragrunt module list - {excluded_terragrunt_modules_list}")

    for exclude_folder in excluded_terragrunt_modules_list:
        terragrunt_ignore_dirs.append('--terragrunt-exclude-dir')
        terragrunt_ignore_dirs.append(exclude_folder)

    logging.debug(f"terragrunt_ignore_dirs - {terragrunt_ignore_dirs}")

    # Set the environment variable required by the terragrunt
    os.environ["TF_VAR_aws_profile"] = profile
    os.environ["AWS_PROFILE"] = profile
    os.environ["ENV"] = env
    os.environ["TF_VAR_aws_region"] = region
    os.environ["CONFIG_FILE"] = f"template_{env}_{region}.yml"
    os.environ["CONFIG_DIR"] = f"{config_dir}"

    # quick hack to fix this warning:
    # WARN[0000] 'plan-all' is deprecated. Running 'terragrunt run-all plan' instead. Please update your workflows
    # to use 'terragrunt run-all plan', as 'plan-all' may be removed in the future!
    if action == "plan-all":
        action = "run-all plan"

    terragrunt_command = ['terragrunt', action]
    terragrunt_command.extend(terraform_args)
    terragrunt_command.extend(terragrunt_ignore_dirs)
    # Format the terragrunt hcl file
    os.system('terragrunt hclfmt')
    os.system(' '.join(terragrunt_command))


def main():
    options = tghelper()
    global env, region
    env = options.env
    region = options.region
    terraform_args = options.args.split(' ')
    if options.verbosity != 0:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
        terraform_args = "--terragrunt-log-level debug --terragrunt-debug"
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    run_terragrunt(action=str(options.action), config_dir=options.config_dir, config_template=options.config_template,
                   env=env, profile=options.profile, region=region, terraform_args=terraform_args,
                   tg_mod_dir=options.tg_dir)


if __name__ == "__main__":
    sys.exit(main())

import argparse


def tghelper():
    """
    Helper function
    :return: Arguments
    """
    parser = argparse.ArgumentParser(description="Terragrunt wrapper to deploy the infrastructure in AWS",
                                     prog="tgwrapper", epilog="Default PROJECT_ROOT is current directory, \
                                     please set it appropriately where your config dir exists")
    parser.add_argument('--action', '-a', help='Terragrunt action.',
                        choices=["init", "plan", "plan-all", "apply",
                                 "apply-all", "destroy", "output", "hclfmt", "state", "import"], required=True)
    parser.add_argument('--args', default='', help='Terraform extra args.')
    parser.add_argument('--config_dir', '-d', help='Name of config directory.', required=False, default='config')
    parser.add_argument('--config_template', '-c', help='Name of config template file.', required=False,
                        default='template.yml')
    parser.add_argument('--env', '-e', help='Target environment.', required=True)
    parser.add_argument('--profile', '-p', help='AWS profile.', required=True)
    parser.add_argument('--region', '-r', help='AWS region.', required=True)
    parser.add_argument('--tg_dir', '-t', help='Terragrunt module directory', default="terragrunt_modules", required=False)
    parser.add_argument('--verbosity', '-v', help='Enable debug.', type=int, default=0, required=False)

    options = parser.parse_args()
    return options

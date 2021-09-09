
## mob-terragrunt-wrapper  
  
Terragrunt wrapper for AWS infra deployment  
  
### How to install  
  
##### Package manager  
```shell script  
 $ pip3 install tgwrapper 
 $ pip3 install --upgrade tgwrapper      # To upgrade
 ```  
 
### Usage  

`tgwrapper` is wrapper over [terragrunt](https://terragrunt.gruntwork.io/) to facilitate in provisioning the scalable infrastructure eg. multi regional, multi environment.

The wrapper can be run by using following command - 
```$ tgwrapper -e networking -r eu-west-1 -p temp_kib-nw -a apply```

```
usage: tgwrapper [-h] --action {init,plan,plan-all,apply,apply-all,destroy,output,hclfmt,state,import} [--args ARGS] [--config_dir CONFIG_DIR][--config_template CONFIG_TEMPLATE] --env ENV --profile PROFILE --region REGION [--tg_dir TG_DIR] [--verbosity VERBOSITY]
Terragrunt wrapper to deploy the infrastructure in AWS

optional arguments:
  -h, --help            show this help message and exit
  --action {init,plan,plan-all,apply,apply-all,destroy,output,hclfmt,state,import}, -a {init,plan,plan-all,apply,apply-all,destroy,output,hclfmt,state,import}
                        Terragrunt action.
  --args ARGS           Terraform extra args.
  --config_dir CONFIG_DIR, -d CONFIG_DIR
                        Name of config directory.
  --config_template CONFIG_TEMPLATE, -c CONFIG_TEMPLATE
                        Name of config template file.
  --env ENV, -e ENV     Target environment.
  --profile PROFILE, -p PROFILE
                        AWS profile.
  --region REGION, -r REGION
                        AWS region.
  --tg_dir TG_DIR, -t TG_DIR
                        Terragrunt module directory
  --verbosity VERBOSITY, -v VERBOSITY
                        Enable debug.

Default PROJECT_ROOT is current directory, please set it appropriately where your config dir exists
```
In order to keep the infrastructure clean, it works on a specific repository structure.

Here is the example of how the repository structure would look like, it may vary depending on your configuration parameters. 

```
.
├── config
│   ├── dev_override.yml
│   ├── sit_override.yml
│   ├── template.yml
├── empty.yaml
└── terragrunt_modules
    ├── global
    │   ├── iam
    │   │   ├── RoleEKSControl
    │   │   │   ├── init.tf
    │   │   │   ├── terragrunt.hcl
    │   │   │   └── versions.tf
    │   │   └── RoleEksWorker
    │   │       ├── init.tf
    │   │       └── terragrunt.hcl
    ├── main.tf
    ├── region.yaml
    ├── regional
    │   ├── vpc_app_1
    │   │   ├── networking
    │   │   │   ├── init.tf
    │   │   │   ├── terragrunt.hcl
    │   │   │   └── versions.tf
    │   ├── vpc_app_2
    │   │   ├── networking
    │   │   │   ├── init.tf
    │   │   │   ├── terragrunt.hcl
    │   │   │   └── versions.tf
    ├── terragrunt.hcl
```
The two important directory `config` and `terragrunt_modules` are required.

The config directory contains two type of files - 
 
 - *Common template file*: 
	 - eg. `template.yml` which consists of common variables 
		 ```

		common_tags: &common_tags
		  Organization: "Mob - Smruti"
		  Terraform: "true"
		  ManagedBy: "iam@gmail.com"
		  
		terragrunt_modules_settings:
		  regional:
		    vpc_app_1:
		      networking:
		        repo: "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git//?ref=v2.24.0"
		        enable_nat_gateway: false
		        single_nat_gateway: false
		        tags:
		          <<: *common_tags
	
		      vpc_app_2:
			      networking:
			        repo: "git::https://github.com/smruti-21/terraform_modules.git//transit_gateway_attachment?ref=v0.3"
			        tags:
			          <<: *common_tags
          ```
          
          **Note:**  The element hierarchy in above file should always be identical with the directory structure where your `terragrunt.hcl` file resides at the sub-module level.
Let's consider above config file, the folder structure for the terragrunt modules will be - 
`terragrunt_modules_settings/regional/vpc_app_1/networking` 
After `networking` element, all others are input parameters to `terragrunt.hcl` file.  
See below for one example of  `terragrunt.hcl` file.

          
 - *Environment override file*: 
 This is actually a jinja template though the extension is yml and the file name should always be `<environment>_override.yml`
	 - eg. `sit_override.yml` environment specific infrastructure configuration are placed in here. 
	 It will render the values from common template file `template.yml` . *By default, override files will get preference over template file.*  
	 
	 Example of <env\>_override file 

```	 
env_settings:
  terragrunt_modules_settings: &settings
    regional:
      vpc_app_1:
        {% set tag_prefix = 'vpc-squid' %}
        {% set cidr = "10.70.87.0/24" %}

          networking:
            default_vpc_name: "{{ tag_prefix }}"
            enable_dns_hostnames: true
            cidr_prefix: {{ cidr.split('.')[1] }}
            cidr: {{ cidr }}
            azs: ["{{ AWS_REGION }}a", "{{ AWS_REGION }}b", "{{ AWS_REGION }}c"]
            private_subnets:
              - "{{ cidr.split('.')[0:3] | join('.') }}.0/27"
              - "{{ cidr.split('.')[0:3] | join('.') }}.32/27"
              - "{{ cidr.split('.')[0:3] | join('.') }}.64/27"
            public_subnets:
              - "{{ cidr.split('.')[0:3] | join('.') }}.96/27"
              - "{{ cidr.split('.')[0:3] | join('.') }}.128/27"
              - "{{ cidr.split('.')[0:3] | join('.') }}.160/27"
            enable_ipv6: false
            enable_nat_gateway: true
            single_nat_gateway: true
            public_subnet_tags:
              Name: "{{ tag_prefix }}-public-subnet"
            private_subnet_tags:
              Name: "{{ tag_prefix }}-private-subnet"
            tags:
              Name: "{{ tag_prefix }}"
  regions:
    eu-west-1:
      <<: *settings

    eu-central-1:
      <<: *settings
		
```
The first 3 elements and last elements are mandatory parameters.
====> _first 3 elements_
```
env_settings:
  terragrunt_modules_settings: &settings
    regional:
```
====> _last 2 elements_
```
regions:
    eu-west-1:
      <<: *settings
```
The wrapper will generate a merged config file based on the AWS region where it will be deployed.
The _regions_ element will get higher preference over _env_settings-> terragrunt_modules_settings ->regional_. If your configuration is different in every region then it can be specified here.  You can manipulate your variable in several ways depending on your requirement. Just to note apart from the standard elements mentioned above, the merge(overwrite if element found) flow is - 
*Regions -> env_settings/terragrunt_modules_settings/(Regional/Global)* <==== (In SIT override file)
SIT override file will get the values from `template.yml` (if required) otherwise the elements of `template.yml` will be merged into override file. Look the examples [here](https://github.com/smruti-21/mob-terragrunt-wrapper/tree/main/example). 

Following is an example, where the derived config file will have default cidr for `eu-central-1` and `100.10.10.0/24` for `eu-west-1`

eg. 
```
regions:
    eu-west-1:
       vpc_app_1:
       {% set cidr = "100.10.10.0/24" %}
	        networking:
	          enable_dns_hostnames: true
	          cidr_prefix: {{ cidr.split('.')[1] }}
	          cidr: {{ cidr }}
	          azs: ["{{ AWS_REGION }}a", "{{ AWS_REGION }}b", "{{ AWS_REGION }}c"]
	          private_subnets:
	            - "{{ cidr.split('.')[0:3] | join('.') }}.0/27"
	            - "{{ cidr.split('.')[0:3] | join('.') }}.32/27"
	            - "{{ cidr.split('.')[0:3] | join('.') }}.64/27"
	          public_subnets:
	            - "{{ cidr.split('.')[0:3] | join('.') }}.96/27"
	            - "{{ cidr.split('.')[0:3] | join('.') }}.128/27"
	            - "{{ cidr.split('.')[0:3] | join('.') }}.160/27"
regions:
    eu-central-1:
    <<: *settings
```
The generated config file will be parsed as input parameter to terragrunt.

Here is an example of sample `terragrunt.hcl` file.
```
locals {
  terragrunt_modules = run_cmd("--terragrunt-quiet", "bash", "-c", "echo -n $(basename ${get_terragrunt_dir()})")
  full_path          = run_cmd("--terragrunt-quiet", "bash", "-c", "echo -n $(dirname ${get_terragrunt_dir()})")
  parent_folder      = run_cmd("--terragrunt-quiet", "bash", "-c", "echo -n $(basename ${local.full_path})")
  tag                = run_cmd("--terragrunt-quiet", "bash", "-c", "echo -n ${local.parent_folder} | sed -e s/_/-/g")
  conf_location      = run_cmd("--terragrunt-quiet", "bash", "-c", "echo -n $(dirname ${find_in_parent_folders("empty.yaml")})/${get_env("CONFIG_DIR")}/${get_env("CONFIG_FILE")}")
  scope              = run_cmd("--terragrunt-quiet", "bash", "-c", "pwd | grep '/global/' >>/dev/null  && echo global || echo regional ")
  conf               = yamldecode(file("${local.conf_location}"))
}

remote_state {
  backend = "s3"

  config = {
    encrypt        = true
    bucket         = "${get_aws_account_id()}-${get_env("TF_VAR_aws_region", "")}-tfstate"
    key            = "${local.scope}/${local.parent_folder}/${local.terragrunt_modules}/terraform-${get_env("ENV", "")}-${get_env("TF_VAR_aws_region", "")}.tfstate"
    region         = "${get_env("TF_VAR_aws_region", "")}"
    dynamodb_table = "dynamo_lock_table"
    profile        = "${get_env("TF_VAR_aws_profile", "")}"
  }
}

terraform {
  source = local.conf["terragrunt_modules_settings"]["${local.scope}"]["${local.parent_folder}"]["${local.terragrunt_modules}"]["repo"]
  before_hook "before_hook" {
    commands = ["apply", "plan"]
    execute  = ["echo", "---------------START: ${local.parent_folder}/${local.terragrunt_modules} ----------------- "]
  }

  after_hook "after_hook" {
    commands     = ["apply", "plan"]
    execute      = ["echo", "---------------END: ${local.parent_folder}/${local.terragrunt_modules} ----------------- "]
    run_on_error = true
  }
}

inputs = merge(
  local.conf["terragrunt_modules_settings"]["${local.scope}"]["${local.parent_folder}"]["${local.terragrunt_modules}"]["tf_variables"],
  {
    tags = {
      Name = "${local.tag}"
    }
  },
  {
    name = "${local.tag}"
  },
)
```

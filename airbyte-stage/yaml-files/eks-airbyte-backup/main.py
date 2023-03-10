import json
import os
import requests
from datetime import datetime, timedelta

import boto3

import helpers

slack_webhook = 'https://hooks.slack.com/services/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'

#Use different values if the env variable is set as test
environment = os.environ['AWS_COST_PROJECT']
print(f'The current environment is {environment}')

if environment == 'TEST':
    with open('.env', 'r') as fh:
        credentials = dict(
            tuple(line.replace('\n', '').split('='))
            for line in fh.readlines() if not line.startswith('#')
        )

#Variables for dates and account id

if environment == 'TEST':
    last_date = credentials['LAST_DATE']
    first_date = credentials['FIRST_DATE']

elif environment == 'PROD':
    last_date = datetime.today() - timedelta(days = 1)
    last_date = last_date.strftime('%Y-%m-%d')

    first_date = datetime.today() - timedelta(days = 7)
    first_date = first_date.strftime('%Y-%m-%d')

time_period = {}
time_period['Start'] = first_date
time_period['End'] = last_date

if environment == 'TEST':
    account_id = credentials['CURRENT_ACCOUNT_ID']
elif environment == 'PROD':
    account_id = boto3.client('sts').get_caller_identity().get('Account') 

if account_id == '814670874755':
    account_id += ' eks-prod'
elif account_id == '686989420008':
    account_id += ' eks-stg'

#Starting the cost_explorer session. If it's in the test env, it will always connect to the stg environment,
#otherwise it will connect to the respective account

if environment == 'TEST':
    print('Using test environment - stg')
    session = boto3.Session(profile_name = 'aws-quext-development')
elif environment == 'PROD':
    session = boto3.Session()
ce_client = session.client('ce')

print(f'Costs explorer client has been instanciated')

#Defining to which dimension will the values be grouped by

group_by_dict = [
    {'Type': 'DIMENSION',
     'Key': 'SERVICE'}
]

aws_costs = ce_client.get_cost_and_usage(
    TimePeriod = time_period, 
    Granularity = 'DAILY', 
    Metrics = ['UnblendedCost'], 
    GroupBy = group_by_dict)

#Creating the variables related to the actual costs
aws_costs_treated = helpers.organize_aws_costs(aws_costs)
aws_ordered_costs, aws_total_costs = helpers.order_and_sum_dict(aws_costs_treated)
aws_top_costs = helpers.return_top_costs(aws_ordered_costs, 5)

print(f'Costs and top costs calculated, total_costs: {aws_total_costs}')

#Adding the variables related to the week before last
if environment == 'TEST':
    last_date_before = credentials['LAST_DATE_BEFORE']
    first_date_before = credentials['FIRST_DATE_BEFORE']

elif environment == 'PROD':
    last_date_before = datetime.today() - timedelta(days = 8)
    last_date_before = last_date_before.strftime('%Y-%m-%d')

    first_date_before = datetime.today() - timedelta(days = 14)
    first_date_before = first_date_before.strftime('%Y-%m-%d')

time_period_before = {}
time_period_before['Start'] = first_date_before
time_period_before['End'] = last_date_before

aws_costs_before = ce_client.get_cost_and_usage(
    TimePeriod = time_period_before, 
    Granularity = 'MONTHLY', 
    Metrics = ['UnblendedCost'], 
    GroupBy = group_by_dict)

aws_costs_before_treated = helpers.organize_aws_costs(aws_costs_before)
_, aws_total_costs_before = helpers.order_and_sum_dict(aws_costs_before_treated)

print(f'Costs for previous week already calculated, total_costs: {aws_total_costs_before}')

aws_cost_difference = aws_total_costs - aws_total_costs_before
aws_cost_difference_percentage = (aws_total_costs / aws_total_costs_before) - 1

#Hitting Kubecost API

kubecost_api_path = os.environ['KUBECOST_NODE_IP'] + '/model/allocation?window=7d&aggregate=namespace'

response = requests.get(
    kubecost_api_path,
    headers = {'Content-Type': 'application/json'}
)

kubecost_original_costs = response.json()
kubecost_costs_treated = helpers.organize_kubecost_costs(kubecost_original_costs)
kubecost_ordered_costs, kubecost_total_costs = helpers.order_and_sum_dict(kubecost_costs_treated)
kubecost_top_costs = helpers.return_top_costs(kubecost_ordered_costs, 5)
kubecost_idle = kubecost_ordered_costs['__idle__']

#Writing the slack text messages
text_messages_list = []

text_messages_list.append(f'Costs report for account *{account_id}* between \
dates *{first_date}* and *{last_date}*')
text_messages_list.append(f'Total cost: *USD {aws_total_costs:.2f}*')
text_messages_list.append(f"""Top 5 services sorted by *cost*: \n {aws_top_costs}""")
if aws_cost_difference > 0:
    word_choice = 'increased'
else:
    word_choice = 'decreased'
text_messages_list.append(f'Compared to the week before ({first_date_before} to {last_date_before}), costs {word_choice} by *USD {aws_cost_difference:.2f}*, a {aws_cost_difference_percentage * 100:.2f}% difference')

text_messages_list.append(f'Regarding only Kubernetes costs, the total cost is: *USD {kubecost_total_costs:.2f}*')
text_messages_list.append(f"""Top 5 services sorted by *cost*: \n {kubecost_top_costs}""")
text_messages_list.append(f'Which means that the idle costs represent *{(kubecost_idle / kubecost_total_costs) * 100:.2f}%* of the total in K8s and *{(kubecost_idle / aws_total_costs) * 100:.2f}%* of the total in the AWS account')

slack_message = helpers.define_slack_message(text_messages_list)

response = requests.post(
    slack_webhook, data = json.dumps(slack_message),
    headers = {'Content-Type': 'application/json'}
)

if response.status_code != 200:
    raise ValueError(f'Slack message could not be sent as the status \
                     is {response.status_code}')









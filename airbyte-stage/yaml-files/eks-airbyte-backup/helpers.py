import json
from typing import Tuple

def organize_aws_costs(original_costs: dict) -> float:
    #Extract the costs by service from the dict
    #made available from AWS API in an ordered way

    costs_treated = {}
    day = 0

    #Looping through every day of code and through services,
    #adding them respecitively
    while day < len(original_costs['ResultsByTime']):
        for service_cost in original_costs['ResultsByTime'][day]['Groups']:
            service = service_cost['Keys'][0]
            service_cost = service_cost['Metrics']['UnblendedCost']['Amount']
            if service not in costs_treated:
                costs_treated[service] = float(service_cost)
            else:
                costs_treated[service] += float(service_cost)
        day += 1   

    return costs_treated

def organize_kubecost_costs(original_costs: dict) -> float:
    #Extract the costs by namespace from the dict
    #made available from Kubecost API in an ordered way

    counter = 0
    costs_treated = {}

    while counter < len(original_costs['data']):
        if counter == 0:
            for key, value in original_costs['data'][counter].items():
                costs_treated[key] = value['totalCost']
        else:
            for key, value in original_costs['data'][counter].items():
                costs_treated[key] += value['totalCost']
                
        counter += 1

    return costs_treated

def order_and_sum_dict(costs: dict) -> Tuple[dict, float]:
    #Return a dict with their respective services and values summed
    #and ordered. Input has to be in this format:
    #{service1: 10.5, service2: 18, service3: 4}

    ordered_costs = {}
    higher_cost = 0
    total_costs = 0
    original_dict_len = len(costs.items())
    
    #Ordering the dict and summing the total value
    while len(ordered_costs.items()) < original_dict_len:

        for service, cost in costs.items():
            if float(cost) > higher_cost:
                higher_cost = float(cost)
                higher_service = service
        
        if higher_cost == 0:
            break
            
        total_costs += higher_cost
        
        ordered_costs[higher_service] = round(higher_cost, 2)

        costs.pop(higher_service)
        higher_cost = 0

    total_costs = round(total_costs, 2)

    return ordered_costs, total_costs

def return_top_costs(ordered_costs: dict, top_n: int) -> str:
    #Return the top n services with their respective
    #costs as string

    top_costs = ''
    counter = 0

    for service, value in ordered_costs.items():
        counter += 1
        top_costs += f'{service} - *USD ' + '{:.2f}'.format(value) + '* \n'
        if counter == top_n:
            break
        
    return top_costs

def define_slack_message(list_of_texts: list) -> str:
    #Creates the actual slack message that will be
    #sent trough slack webhook API
    
    first_part_of_message = """{
              "channel": "#quext-cost-reporting",
                        "username": "AWS Cost Monitor",
        "blocks": ["""

    last_part_of_message = """{
                "type": "divider"
            }
        ]

    }"""

    middle_part_of_message = ""

    for text in list_of_texts:
        middle_part_of_message = """%(previous_message)s 
                    {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "%(text)s"
                }
            },
        """ % {'previous_message': middle_part_of_message, 'text': text}

    slack_message = f'{first_part_of_message} {middle_part_of_message} {last_part_of_message}'
    print(slack_message)
    slack_message = json.loads(slack_message, strict = False)

    return slack_message





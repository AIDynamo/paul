# import necessary libraries
import json
import os
import sys

import pandas as pd
import requests
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

FIRST_TEAM = 27
SECOND_TEAM = 17

predictable_fields = [
    'yellow_cards',
    'red_cards',
    'substitutions',
    'possesion',
    'free_kicks',
    'goal_kicks',
    'throw_ins',
    'offsides',
    'corners',
    'shots_on_target',
    'shots_off_target',
    'attempts_on_goal',
    'saves',
    'fauls',
    'treatments',
    'penalties',
    'shots_blocked',
    'dangerous_attacks',
    'attacks',
]

teamed_predictable_fields = []

for field in predictable_fields:
     for team_name in ['team1', 'team2']:
        teamed_predictable_fields.append(team_name + '_' + field)
teamed_predictable_fields.append('team1_score')
teamed_predictable_fields.append('team2_score')

# load the data
data = requests.get(
    os.getenv('API_BASE_URL') + '/get-h2h?team_1=' + str(FIRST_TEAM) + '&team_2=' + str(SECOND_TEAM)).json()

matches = data['team1_last_6'] + data['team2_last_6'] + data['h2h']
filtered_rows = []

for key, match in enumerate(matches):
    first_team_index = 0 if match['home_id'] == str(FIRST_TEAM) else 1
    second_team_index = 1 if match['home_id'] == str(FIRST_TEAM) else 0

    filtered_match = {
        'month': match['date'].split('-')[1],
        'home_id': match['home_id'],
        'away_id': match['away_id'],
        'competition_id': match['competition_id'],

        'team1_score': match['score'].split(' - ')[first_team_index],
        'team2_score': match['score'].split(' - ')[second_team_index],
    }

    if 'yellow_cards' in match['stats']:
        for team_name in ['team1', 'team2']:
            team_index = first_team_index if team_name == 'team1' else second_team_index
            for field in predictable_fields:
                filtered_match[team_name + '_' + field] = match['stats'][field].split(':')[team_index] if \
                    match['stats'][field] is not None else 0
    else:
        for team_name in ['team1', 'team2']:
            for field in predictable_fields:
                key = team_name + '_' + field
                if key not in filtered_match:
                    filtered_match[key] = 0

    filtered_rows.append(filtered_match)

# pprint(filtered_rows)
# sys.exit()

# convert the data into a dataframe
df = pd.DataFrame(filtered_rows)
# get the necessary columns
X = df[['home_id', 'away_id', 'competition_id', 'month']]
y = df[teamed_predictable_fields]

# split the data into training and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, train_size=0.9, random_state=0)

# create and fit the model
model = LinearRegression()
model.fit(X_train.values, y_train.values)

# predict the upcoming match final result
# home_id ,away_id ,competition_id ,month
upcoming_match = [[FIRST_TEAM, SECOND_TEAM, 244, 4]]
prediction = model.predict(upcoming_match)

for key, field_name in enumerate(teamed_predictable_fields):
    print(field_name + ': ' + str(prediction[0][key]))

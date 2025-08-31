import os
import pandas as pd
import json
import re
import sqlite3
from collections import Counter

# Jupyter Lab hack
__file__ = os.path.abspath('')
PREFIXPATH = f'{os.getcwd()}'
## --------------------------- #
## import raw interaction data
## --------------------------- #

### TODO: load fresh database when users request scorecard
### TODO: metadata and mapping dynamic generation at first startup.
###########################################################
DB_FILE = f"{PREFIXPATH}/reviews.db"


json_file_path = f'{PREFIXPATH}/../DataAnalysis/WISE/metadata_e45a6b1bf592124c83d2423097c65ab39d545e4b.json'
mapping_path = f'{PREFIXPATH}/../DataAnalysis/WISE/cwe_pillar_and_category.csv'


def load_db():
  fname = DB_FILE.split('/')[-1] # extract filename
  conn = sqlite3.connect(DB_FILE)

  df_raw = pd.read_sql_query("SELECT * FROM review;", conn)
  df_raw['run'] = fname.split('__')[0]

  conn.close()

  # Ensure JSON column is parsed correctly
  df_raw['sol_user'] = df_raw['sol_user'].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else {})
  return df_raw

###########################################################

def get_db_and_uuidCookie_interactions(uuidCookie):
  df_raw=load_db()
  user_df = df_raw[df_raw['uuidCookie'] == uuidCookie]

  return df_raw, user_df

# Flatten the metadata
def flatten_dict(d, parent_key='', sep='-', exceptions=['sol_intended']):
  items = []
  for k, v in d.items():
    new_key = parent_key + sep + k if parent_key else k
    if isinstance(v, dict) and k not in exceptions:
      items.extend(flatten_dict(v, new_key, sep=sep).items())
    elif k in exceptions:
      sol_intended_entries = {}
      for line_num, text in v.items():
        if ' @@TAGS ' in text:
          solution_text, tags_part = text.split(' @@TAGS ')
          cwe_tags = [tag.strip() for tag in tags_part.split(', ')]
        else:
          solution_text = text.strip()
          cwe_tags = []
        sol_intended_entries[line_num] = {
          "solution_text": solution_text.strip(),
          "cwe": cwe_tags
        }
      items.append((new_key, sol_intended_entries))
    else:
      items.append((new_key, v))
  return dict(items)

# Extract CWE metadata
def clean_cwe(cwe):
  match = re.match(r"(CWE-\d+)", cwe)
  return match.group(1) if match else None

def extract_cwe_metadata():
  exercises_cwe_metadata = {}
  overall_cwe = []

  with open(json_file_path, 'r') as file:
    metadata = json.load(file)

  flattened_metadata = {exercise_uuid: flatten_dict(metadata_dict) for exercise_uuid, metadata_dict in metadata.items()}

  for key, data in flattened_metadata.items():
    sol_intended = data.get("sol_intended", {})
    cwe_list_dict = {}

    for sub_key, value in sol_intended.items():
      clean_cwe_list = [clean_cwe(cwe) for cwe in value["cwe"]]
      clean_cwe_list = [cwe for cwe in clean_cwe_list if cwe]
      cwe_list_dict[sub_key] = clean_cwe_list

    all_cwe = [cwe for cwe_list in cwe_list_dict.values() for cwe in cwe_list]
    cwe_list_dict["all_cwe"] = all_cwe
    exercises_cwe_metadata[key] = cwe_list_dict
    overall_cwe.extend(all_cwe)

  exercises_cwe_metadata["overall_cwe"] = overall_cwe

  return exercises_cwe_metadata

def group_attempts(user_df):
  # Process the data to split into groups based on first vs. multiple attempts
  filtered_solve_attempts = user_df[user_df['interactType'] == 'submitButtonClicked']

  # Group by user (uuidCookie) and exerciseUUID
  grouped = filtered_solve_attempts.groupby(['uuidCookie', 'exerciseUUID'])

  # Determine first and multiple attempts
  group_data = []
  for (user, exercise), group in grouped:
    group = group.sort_values(by='interactTime')  # Ensure order by time
    first_attempt_solved = group.iloc[0]['solved'] == 1
    multiple_attempts_solved = group['solved'].sum() > 0 and not first_attempt_solved
      
    if first_attempt_solved:
      group_data.append({'uuidCookie': user, 'exerciseUUID': exercise, 'solved_on_first_attempt': True})
    elif multiple_attempts_solved:
      group_data.append({'uuidCookie': user, 'exerciseUUID': exercise, 'solved_on_first_attempt': False})

  # Create a combined DataFrame
  combined_attempts = pd.DataFrame(group_data)

  return combined_attempts

# Compute seen CWEs
def compute_seen_cwes(row, uuidCookie):
  user_id = row['uuidCookie']
  exercise_id = row['exerciseUUID']
  solved_on_first_attempt = row['solved_on_first_attempt']

  df_raw, user_df = get_db_and_uuidCookie_interactions(uuidCookie)

  # Process the data to split into groups based on first vs. multiple attempts
  filtered_solve_attempts = user_df[user_df['interactType'] == 'submitButtonClicked']
  exercises_cwe_metadata = extract_cwe_metadata()

  if solved_on_first_attempt:
    user_submissions = filtered_solve_attempts[
      (filtered_solve_attempts['uuidCookie'] == user_id) & 
      (filtered_solve_attempts['exerciseUUID'] == exercise_id)
    ]
    sol_user_keys = user_submissions['sol_user'].dropna().apply(lambda x: max(eval(x).keys(), default=0))
    max_key = max(sol_user_keys, default=0)
    if exercise_id in exercises_cwe_metadata:
      seen_cwes = []
      for k, cwe_list in exercises_cwe_metadata[exercise_id].items():
        if k != "all_cwe" and k.isdigit() and int(k) <= int(max_key):
          seen_cwes.extend(cwe_list)
    else:
      seen_cwes = []
  else:
    seen_cwes = exercises_cwe_metadata.get(exercise_id, {}).get("all_cwe", [])
  
  return seen_cwes

def get_cwe_statistics(uuidCookie = None):
  df_raw, user_df = get_db_and_uuidCookie_interactions(uuidCookie)
  
  if not uuidCookie:
    user_df = df_raw
  
  combined_attempts = group_attempts(user_df)
  combined_attempts['seen_cwes'] = combined_attempts.apply(compute_seen_cwes, uuidCookie=uuidCookie, axis=1)

  # Build the normalization vector
  all_seen_cwes = [cwe for cwe_list in combined_attempts['seen_cwes'] for cwe in cwe_list]
  cwe_counter = Counter(all_seen_cwes)
  total_cwes = sum(cwe_counter.values())
  normalization_vector = {cwe: count / total_cwes for cwe, count in cwe_counter.items()}

  # Output the normalization vector
  normalization_vector_df = pd.DataFrame(list(normalization_vector.items()), columns=['CWE', 'Normalized_Value'])
  # sorted_cwe_df = normalization_vector_df.sort_values(by='Normalized_Value', ascending=False).reset_index(drop=True)

  max_value = normalization_vector_df['Normalized_Value'].max()
  normalization_vector_df['Max_Normalized_Value'] = normalization_vector_df['Normalized_Value'] / max_value

  # Rename 'CWE-ID' to 'CWE' for consistency before merging
  cwe_additional_data = pd.read_csv(mapping_path)
  cwe_additional_data.rename(columns={'CWE_ID': 'CWE'}, inplace=True)

  # Merge the normalization vector DataFrame with the additional data
  merged_cwe_data = normalization_vector_df.merge(cwe_additional_data, on='CWE', how='left')

  parent_grouped = merged_cwe_data.groupby('Parent_1400').agg(
    Normalized_Sum=('Normalized_Value', 'sum'),
    Parent_1400_text=('text_1400', 'first')
  )
  parent_grouped['Normalized_Sum'] = parent_grouped['Normalized_Sum'] / parent_grouped['Normalized_Sum'].sum()
  parent_grouped.sort_values(by="Normalized_Sum", ascending=False, inplace=True)
  parent_grouped.reset_index(inplace=True)
  parent_grouped.to_csv('normalisation_CWE.csv', index=False)

  pillar_grouped = merged_cwe_data.groupby('Pillar_1000').agg(
    Normalized_Sum=('Normalized_Value', 'sum'),
    Pillar_1000_text=('Pillar_1000_text', 'first')
  )
  pillar_grouped['Normalized_Sum'] = pillar_grouped['Normalized_Sum'] / pillar_grouped['Normalized_Sum'].sum()
  pillar_grouped.sort_values(by="Normalized_Sum", ascending=False, inplace=True)
  pillar_grouped.reset_index(inplace=True)

  return parent_grouped, pillar_grouped
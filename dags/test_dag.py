import pandas as pd
from sqlalchemy import create_engine, text
from airflow import DAG
from airflow.models import Variable
from datetime import timedelta, datetime
from airflow.operators.python import PythonOperator
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

log = logging.getLogger(__name__)


def import_email_appeals():

    log.info("Pulling data from G-Sheets")

    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        eval(Variable.get("ppl_g_sheets_credentials_token")), scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("appeals@invisible.email").worksheet('Sheet1')
    data = wks.get_all_values()
    headers = data.pop(0)

    df = pd.DataFrame(data, columns=headers)
    df.columns = ["email_subject", "rp", "name_of_complaint", "termination_date",
                  "email_received", "category", "reason", "manager", "department",
                  "complaint_resolved", "name_of_rp", "response_date", "note", "na"]
    df = df[['rp', 'email_received', 'category', 'manager', 'department',
             'complaint_resolved', 'name_of_rp', 'response_date']]

    # Change the email_received column from "January 3, 2023" format into a datetime
    df = df.assign(email_received=df['email_received'].apply(lambda x: pd.to_datetime(x, errors='coerce')))

    log.info("Dataframe ready for upload to Invisible DB")

    engine = create_engine(Variable.get("warehouse_people_team_db_uri_token"), echo=False)
    df.to_sql('email_appeals', con=engine, if_exists="replace", index=True)

    sql_script = """
    GRANT DELETE, TRUNCATE, INSERT, SELECT, UPDATE, REFERENCES,
    TRIGGER ON TABLE people_team.email_appeals TO analyst;
    GRANT DELETE, TRUNCATE, INSERT, SELECT, UPDATE, REFERENCES,
    TRIGGER ON TABLE people_team.email_appeals TO metabase;
    GRANT DELETE, TRUNCATE, INSERT, SELECT, UPDATE, REFERENCES,
    TRIGGER ON TABLE people_team.email_appeals TO reporting;"""

    with engine.connect() as conn:
        conn.execute(text(sql_script))

    log.info("Dataframe uploaded to Invisible DB and permissions granted")


default_args = {
    'owner': 'anddy0622@gmail.com',
    'depends_on_past': False,
    'email': ['anddy0622@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    "email_appeals",
    start_date=datetime(2022, 6, 1, 17, 15),
    default_args=default_args,
    schedule_interval="0 12 * * *",
    catchup=False
) as dag:

    uploading_data = PythonOperator(
        task_id="email_appeals",
        python_callable=import_email_appeals
    )

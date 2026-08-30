
from app.tools.sql_tool import execute_sql


rows = execute_sql(
    "SELECT * FROM survey_responses LIMIT 5"
)

print("\nDatabase results:")

for row in rows:
    print(row)


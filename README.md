# main.py helpers

This small helper script contains functions to:

- store a pandas DataFrame into MySQL (`store_to_mysql`)
- prompt the user for an insight request (`get_user_query`)
- generate a SQL query from a natural language question using OpenAI (`generate_sql_query`)

Security notes
--------------

Do NOT hardcode your OpenAI API key in source code. This project supports three ways to provide the key (in order of preference):

1. Set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

2. Create a `.env` file in the project directory with the following content (requires `python-dotenv`):

```
OPENAI_API_KEY=sk-...
```

3. Store the key in the system keyring (requires the `keyring` package). From Python you can use the provided helper:

```python
from main import store_api_key_in_keyring
store_api_key_in_keyring("sk-...")
```

Quick start
-----------

Install requirements (use a virtualenv):

```bash
/usr/local/bin/python3 -m pip install -r /Users/jieunkim/requirements.txt
```

Run the script (it defines functions; it will not call the API by default):

```bash
/usr/local/bin/python3 /Users/jieunkim/main.py
```

Testing `generate_sql_query`
---------------------------

After setting your API key by one of the methods above, call the function from Python to generate a SQL statement:

```python
from main import generate_sql_query
print(generate_sql_query("Show average sales by region", "sales_table"))
```

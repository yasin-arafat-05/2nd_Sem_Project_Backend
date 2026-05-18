
# 1. Command For Windows University Server(GUI):

- search psql then goto the terminal,  then give the necessary information to login.


<br>

# 2. Some basic command that need while developing a project

<br>

- 1. all table list
```bash
\dt
```
- 2. description of a table
```bash
\d table_name
```


<br>

# 3. Database Migration With Alembic:

<br>

Alembic is a lightweight database migration tool for usage with SQLAlchemy. Like git.Why use it? 
-When you change your SQLAlchemy models (add a column, change a relationship), Alembic automatically updates your live PostgreSQL database without losing your existing data.

How it tracks changes: 
- It creates a special folder in your project where it stores every change as a history file (Migration Scripts). <br>
The Workflow:Modify Models ----> Generate Migration Script ----> Apply to Database.

###  How to Create and Run the Migration File
Instead of creating a file named exactly migration.py manually, Alembic uses a command to generate a unique file inside a specific folder. Each file gets a unique ID and timestamp so it doesn't overwrite old history.
Here is the exact step-by-step guide to doing this:

### Step 1: Install Alembic (If not already installed)
Open your Windows CMD inside your project folder and run:
```bash
pip install alembic
```

### Step 2: Initialize Alembic (Only do this once per project)
Run this command to create the setup folders:
```bash
alembic init alembic
```
This will create an alembic.ini file and an alembic/ folder in your project.

### Step 3: Link Alembic to your Database
   1. Open the newly created alembic.ini file.
   2. Find the line starting with sqlalchemy.url.
   3. Change it to match your PostgreSQL configuration:
   
  - sqlalchemy.url = postgresql://postgres:passwrd@localhost:5432/data_name
  - If you have a person config file then remove the code for configuration from env.py of alembic.
   
(Note: You also need to import your Base metadata inside alembic/env.py, but let's look at creating the file first).

### Step 4: Create the Migration File (This is your "migration.py")
Now that your Python code is updated with the ondelete="CASCADE", run this command to generate the migration file:
```bash
alembic revision --autogenerate -m "add_cascade_to_business"
```

* What happens now? Look inside your project folder: alembic/versions/. You will see a brand new file with a name like 1a2b3c4d5e6f_add_cascade_to_business.py. This is your migration file!

### Step 5: Push Changes to PostgreSQL
To execute that migration file and permanently update your database, run:
```python
alembic upgrade head
```







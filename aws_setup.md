<br>
<br>

# `#01: AWS EC2 Basic Set UP:`

<br>
<br>


### **1. Download the `.pem` key after creating EC2 instance**
This key is required to connect to the server.


### **2. Fix permissions for the PEM file (must be done first!)**

```
chmod 400 demo.pem
```

This ensures SSH will accept the key.


### **3. Connect to the EC2 instance via SSH**

```
ssh -i demo.pem ec2-user@13.60.245.240
```


### **4. Transfer local project files to the EC2 server**

Run this command **from your local machine**:

```
scp -i demo.pem -r /home/yasin/all_program/backend/eApp ec2-user@13.60.245.240:/home/ec2-user/eApp
```


### **5. Install PostgreSQL on EC2**

```
sudo dnf install postgresql postgresql-server -y
```


### **6. Initialize PostgreSQL database**

```
sudo postgresql-setup --initdb
```


### **7. Start & enable PostgreSQL service**

```
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **8. Login as postgres user**

```
sudo -iu postgres
psql
```


### **9. Edit pg_hba.conf for authentication**

Path:

```
/var/lib/pgsql/data/pg_hba.conf
```

Edit:

```
sudo nano /var/lib/pgsql/data/pg_hba.conf
```


### **10. Example pg_hba.conf entries**

```
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
```


<br>
<br>

# `#02: If we have more than 1 server than what will you do? Use TMUX`

<br>
<br>


## **1. Sessions**

### Create a new session

```
tmux new -s session_name
```

### List all sessions

```
tmux ls
```

### Attach to a session

```
tmux attach -t session_name
```

### Detach from session (background mode)

```
Ctrl + b , then d
```

### Kill a specific session

```
tmux kill-session -t session_name
```

### Kill all sessions

```
tmux kill-server
```

### Rename current session

```
Ctrl + b , then $
```


## **2. Windows**

### Create a new window in a session

```
Ctrl + b , then c
```

### Switch between windows

```
Ctrl + b , then 0
Ctrl + b , then 1
Ctrl + b , then 2
```

### List windows

```
Ctrl + b , then w
```

### Close current window

```
exit
```


## **3. Panes (Splits)**

### Split terminal vertically (left & right)

```
Ctrl + b , then %
```

### Split terminal horizontally (top & bottom)

```
Ctrl + b , then "
```

### Move between panes

```
Ctrl + b , then ← / → / ↑ / ↓
```

### Resize panes

```
Ctrl + b , then hold Ctrl + arrow key
```

or

```
Ctrl + b , then :resize-pane -L/-R/-U/-D
```

### Close current pane

```
exit
```

or

```
Ctrl + b , then x
```

### Make pane fullscreen (toggle zoom)

```
Ctrl + b , then z
```

### Cycle through layouts (auto arrange panes)

```
Ctrl + b , then Space
```


## **4. Logging / Scroll Mode**

### Enter scroll mode

```
Ctrl + b , then [
```

### Scroll with arrow keys / PageUp / PageDown

### Exit scroll mode

```
q
```


## **5. Useful Production Commands inside tmux**

### **Celery Payment Worker**

```
celery -A eApp.worker.celery_task_payment.celery_app_payment worker --loglevel=info --concurrency=1
```

### **Celery Beat**

```
celery -A eApp.worker.celery_task_payment.celery_app_payment beat --loglevel=info
```

### **Chatbot LLM Worker**

```
celery -A eApp.worker.celery_task_llm.celery_app_llm worker --loglevel=info --pool=solo
```

or

```
celery -A eApp.worker.celery_task_llm.celery_app_llm worker -P prefork --loglevel=INFO --concurrency=2 -Q llm_tasks
```



<br>
<br>

# `#03: Development Mode VS Production MOde Background Process: `

<br>
<br>

## **1. Problem with Development Mode**

When you start the server in dev mode:

```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

* The `--reload` works only while your terminal is active.
* After some time or if the terminal closes, the server **stops or doesn’t reload automatically**.
* Or if we run it background then server still running but don't receive any request.

## **2. Solution: Create a systemd Service**

**Service file example**: `/etc/systemd/system/uvicorn.service`

```
[Unit]
Description=Uvicorn instance for FastAPI app
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/ec2-user/.local/bin/uvicorn eApp.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

<br>

```bash
# get some error havn't solve this issue
eApp.main:app --host 0.0.0.0 --port 8000 --worker 5 

```

<br>


## **3. Key Points About systemd & Daemon**

* **Daemon role**: `systemd` manages background processes (daemons).
* Runs your server **automatically on boot**.
* **Restart=always** ensures the service **restarts if it crashes**.
* `RestartSec=3` waits 3 seconds before restarting to prevent rapid crash loops.
* **Logging**: `StandardOutput=journal` & `StandardError=journal` allows you to check live logs with:

```
journalctl -u uvicorn -f
```


## **4. Commands After Creating Service**

1. Reload systemd to recognize the new service:

```
sudo systemctl daemon-reload
```

2. Start or restart the service:

```
sudo systemctl start uvicorn
sudo systemctl restart uvicorn
```

3. Enable auto-start on boot:

```
sudo systemctl enable uvicorn
```

4. Check live logs:

```
journalctl -u uvicorn -f
```

## **5. Why Use a Service File?**

* Keeps the FastAPI server **running in background**.
* Ensures **automatic restart** if it crashes.
* Allows **centralized logging**.
* Decouples server process from terminal session.




<br>
<br>

# `#4: Celery Worker Command For SSE: `

<br>
<br>


```bash 
celery -A eApp.worker.celery_task_llm.celery_app_llm worker -P prefork --loglevel=INFO --concurrency=2 -Q llm_tasks

```


<br>
<br>

# `#5: Recover Database: `

<br>
<br>



### **PostgreSQL Backup Note (Using pg_dump on EC2)**

I created a full backup of my PostgreSQL database on the AWS EC2 instance using the following command:

```bash
pg_dump -U postgres mydb > mydb_backup.sql
```

After generating the backup file, I downloaded it to my local machine using `scp`:

```bash
scp -i demo.pem ec2-user@13.60.245.240:/home/ec2-user/mydb_backup.sql .
```

This backup file can be restored later on any new EC2 instance (or any PostgreSQL server) with the following command:

```bash
psql -U postgres -d mydb -f mydb_backup.sql
```

<br>
<br>

```bash
❯ sudo -iu postgres              
[postgres@archlinux ~]$ psql
psql (17.6)
Type "help" for help.

postgres=# create database mydb owner ecommerce;
CREATE DATABASE
postgres=# exit
[postgres@archlinux ~]$ exit
logout
                                                                                                                                                                      
~   39s
❯ cd Downloads             
                                                                                                                                                                      
~/Downloads   
❯ psql -U postgres -d mydb -f mydb_backup.sql

SET
SET
SET
SET
SET
 set_config 
------------
 
(1 row)

SET
SET
SET
SET
SET
SET
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE TABLE
ALTER TABLE
CREATE TABLE
ALTER TABLE
CREATE TABLE
ALTER TABLE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
CREATE TABLE
ALTER TABLE
CREATE SEQUENCE
ALTER TABLE
ALTER SEQUENCE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
COPY 3
COPY 814
COPY 10
COPY 2707
COPY 229
COPY 20
COPY 26
COPY 0
COPY 0
COPY 12
COPY 2
COPY 0
COPY 3
 setval 
--------
      3
(1 row)

 setval 
--------
     20
(1 row)

 setval 
--------
     26
(1 row)

 setval 
--------
      1
(1 row)

 setval 
--------
      1
(1 row)

 setval 
--------
     13
(1 row)

 setval 
--------
      3
(1 row)

 setval 
--------
      1
(1 row)

 setval 
--------
      3
(1 row)

ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE

~/Downloads   
❯ ❯ sudo -iu postgres                          
[postgres@archlinux ~]$ psql -h localhost -d mydb
psql (17.6)
Type "help" for help.

mydb=# 
mydb=# \dt;
                 List of relations
 Schema |         Name          | Type  |   Owner   
--------+-----------------------+-------+-----------
 public | business              | table | ecommerce
 public | checkpoint_blobs      | table | ecommerce
 public | checkpoint_migrations | table | ecommerce
 public | checkpoint_writes     | table | ecommerce
 public | checkpoints           | table | ecommerce
 public | conversations         | table | ecommerce
 public | message_history       | table | ecommerce
 public | payment_methods       | table | ecommerce
 public | pricing_config        | table | ecommerce
 public | products              | table | ecommerce
 public | social_media_tokens   | table | ecommerce
 public | subscriptions         | table | ecommerce
 public | users                 | table | ecommerce
(13 rows)

mydb=# select * from users;
 id | username |            email            |                                             password                                              | is_verified |      
   join_date          | free_count | paid_status | role | is_active | last_login 
----+----------+-----------------------------+---------------------------------------------------------------------------------------------------+-------------+------
----------------------+------------+-------------+------+-----------+------------
  2 | Yasin    | yasinarafat.d2021@gmail.com | $argon2id$v=19$m=65536,t=3,p=4$/a4IqbQCvX67i3Nk5DGUsw$Xzjb8S/rEWDwRcgvW/pClz19qU7JcBxDSQ/St1LiJts | t           | 2025-
11-18 17:43:04.605769 |          0 | f           | user | t         | 
  3 | prosen   | prosenjit1156@gmail.com     | $argon2id$v=19$m=65536,t=3,p=4$ayPxr/gagrv4ZMXJTvlleQ$2mT+KpT2fiETS61lFnzzj9cRrpsk1QkH0tDVDvnyk3k | f           | 2025-
11-19 05:05:04.883594 |          3 | f           | user | t         | 
  1 | Yasin    | ug2102030@cse.pstu.ac.bd    | $argon2id$v=19$m=65536,t=3,p=4$33C3J2XaXzgZfcBOds78Gw$ln8kaJPj2SOPkv3c5rHw5dZQ3/+bSzgVJpYIVdN1358 | t           | 2025-
11-18 17:41:38.999952 |          3 | f           | user | t         | 
(3 rows)

mydb=# 

```

<br>
<br>


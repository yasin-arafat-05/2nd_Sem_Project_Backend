# ========= For generating Schema =========
# from eralchemy import render_er
# from eApp.models import Base 
# render_er(Base,'schema.png')  


# ========= For generating Schema Diagram  =========
# from sqlalchemy_schemadisplay import create_schema_graph
# from sqlalchemy import create_engine
# from eApp.database import Base

# # Use SYNC engine (psycopg2), not asyncpg
# DATABASE_URL = "postgresql://ecommerce:ecom12345@localhost:5432/ecom"

# engine = create_engine(DATABASE_URL)

# # Reflect existing tables
# Base.metadata.bind = engine

# graph = create_schema_graph(
#     metadata=Base.metadata,
#     show_datatypes=True,
#     engine=engine,
#     show_indexes=True,
#     rankdir='LR'
# )

# graph.write_png('erd.png')
# print("ERD Generated: erd.png")


# ===== ER diagram, make relationship like strong weak entity like this ========
from graphviz import Digraph

g = Digraph('ERD', format='png')

# -----------------------
# Strong Entities
# -----------------------
g.node('Bank', 'Bank', shape='box')
g.node('Branch', 'Branch', shape='box')
g.node('Loan', 'Loan', shape='box')
g.node('Employee', 'Employee', shape='box')
g.node('Customer', 'Customer', shape='box')
g.node('Account', 'Account', shape='box')

# -----------------------
# Attributes (ellipses)
# -----------------------
g.node('Bname', 'Bname', shape='ellipse')
g.node('code', 'code', shape='ellipse')

g.node('Bcode', 'Bcode', shape='ellipse')
g.node('location', 'location', shape='ellipse')

g.node('loan_no', 'loan_no', shape='ellipse')
g.node('amount', 'amount', shape='ellipse')

g.node('Eid', 'Eid', shape='ellipse')
g.node('salary', 'salary', shape='ellipse')

g.node('Cid', 'Cid', shape='ellipse')
g.node('DOB', 'DOB', shape='ellipse')
g.node('Address', 'Address', shape='ellipse')

g.node('type', 'type', shape='ellipse')
g.node('acc_no', 'acc_no', shape='ellipse')

# -----------------------
# Relationship Diamonds
# -----------------------
g.node('has', 'has', shape='diamond')
g.node('provides', 'provides', shape='diamond')
g.node('works_in', 'works in', shape='diamond')
g.node('contains', 'contains', shape='diamond')
g.node('maintains', 'maintains', shape='diamond')
g.node('avails', 'avails', shape='diamond')
g.node('has2', 'has', shape='diamond')

# -----------------------
# Edges (with cardinalities)
# -----------------------

# Bank
g.edge('Bank', 'Bname')
g.edge('Bank', 'code')

g.edge('Bank', 'has', label='1')
g.edge('has', 'Branch', label='N')

# Branch
g.edge('Branch', 'Bcode')
g.edge('Branch', 'location')

g.edge('Branch', 'works_in', label='1')
g.edge('works_in', 'Employee', label='N')

g.edge('Branch', 'contains', label='M')
g.edge('contains', 'Customer', label='N')

g.edge('Branch', 'maintains', label='1')
g.edge('maintains', 'Account', label='N')

# Loan
g.edge('Loan', 'loan_no')
g.edge('Loan', 'amount')

g.edge('Loan', 'provides', label='1')
g.edge('provides', 'Branch', label='N')

g.edge('Customer', 'avails', label='M')
g.edge('avails', 'Loan', label='N')

# Employee
g.edge('Employee', 'Eid')
g.edge('Employee', 'salary')

# Customer
g.edge('Customer', 'Cid')
g.edge('Customer', 'DOB')
g.edge('Customer', 'Address')

g.edge('Customer', 'has2', label='M')
g.edge('has2', 'Account', label='N')

# Account
g.edge('Account', 'type')
g.edge('Account', 'acc_no')

g.render('bank_erd_diagram', cleanup=True)





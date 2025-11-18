
from eApp import models
from fastapi import FastAPI
from sqlalchemy.sql import text 
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from eApp.workflows.workflow import workflow
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from eApp.database import asyncSession,async_engine,connection_string


#"""
# tables.BASE.metadata.create_all(bind=async_engine): synchronous:
# asynchronous: advance guide: Lifespan fastapi Documentation:
# yeild give the control to fastapi, it's working procedure 
# is different when work with a context manager.
#"""
@asynccontextmanager
async def lifespan(app:FastAPI):
    #--------------------Applicatoin startup------------------
    print("Application startup started")
    global complied_graph
    try:
        # a.Create Database Schema:
        async with async_engine.begin() as conn:
            print("Database connection established")
            await conn.run_sync(fn=models.Base.metadata.create_all)
            print("Application startup completed")
            
        #b.Compile the langgraph checkpointer and keep connection alive for app lifetime:
        psycopg_conn_string =  connection_string.replace("+asyncpg","")
        async with AsyncConnectionPool(
            conninfo=psycopg_conn_string,
            max_size=20,
            kwargs={
                "autocommit":True,
                "prepare_threshold":0,
                "row_factory":dict_row,
            },
        ) as pool:
            app.state.pg_pool = pool
            # keep a dedicated connection for the checkpointer across the app lifetime
            conn = await pool.getconn()
            app.state.pg_conn = conn
            try:
                memory = AsyncPostgresSaver(conn)
                await memory.setup()
                graph = workflow.compile(checkpointer=memory)
                app.state.graph = graph 
            except Exception:
                # return the connection if setup fails
                await pool.putconn(conn)
                app.state.pg_conn = None
                raise
            # hand control to FastAPI while pool/conn contexts remain open
            yield 
            # after application shutdown, return the dedicated connection
            try:
                await pool.putconn(conn)
            except Exception:
                pass
    except Exception as e:
        print(f"Startup error: {e}")
        raise
    
    #--------------------Applicatoin Shutdown------------------
    # when it will execute
    # crtl + c 
    # uvicoron stop 
    print("Application shutdown started")
    try:
        # Pool/connection are closed by the context manager above
        await async_engine.dispose()
        print("Database connections closed")
    except Exception as e:
        print(f"Shutdown error: {e}")
    print("Application shutdown completed")


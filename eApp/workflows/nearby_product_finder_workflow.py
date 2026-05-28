
from dotenv import load_dotenv
from pydantic import BaseModel
from eApp.config import CONFIG
from typing import List,Optional
from langchain_groq import ChatGroq
from eApp.database import asyncSession
from langgraph.graph import StateGraph,START,END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from eApp.routes.categories import fetch_categories_from_db
from eApp.routes.local_search import local_search_llm_context
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage


load_dotenv()
model_name = "llama-3.1-8b-instant"

class AgentState(BaseModel):
    user_question: str 
    current_user_id : int 
    accumulated_info: List[str] = []
    generated_content: str = ""
    product_categry_des: str = None
    router_clarify : bool = False 
    clarification_message: str = ""
    categories_clarification_message: str = ""
    categories_match_or_not: bool = False 
    matches_categories : List[str] = []
    fetch_product_info : List[str] = []
    user_lat : float 
    user_long : float 



# ===================== Node Defination =====================
def analysis_requirements(state:AgentState)->AgentState:
    """
    Docstring for analysis_requirements: (Check wheater user ask for a product or not.)
    :param state: AgentState Pydantic class
    :type state: AgentState
    :return: Updated AgentState
    :rtype: AgentState
    """
    try:
        class OutputSchema(BaseModel):
            local_prod : bool = False 
            product_description: Optional[str] = None 
        system_prompt = (
            "You are an expert AI Routing and Requirement Analysis Agent for a hyperlocal e-commerce platform.\n"
            "Your job is to analyze the user's input, classify their intent, and respond strictly in English.\n\n"
            
            "CRITICAL: Do not add any extra markdown, JSON tags, or formatting outside the function call structure. Provide ONLY the raw structured fields.\n\n" # <--- এই লাইনটি Groq-এর জন্য লাইফসেভার
            
            "Classify the intent into one of these two categories:\n"
            "1. 'local_product_search':\n"
            "   - Choose this if the user is explicitly or implicitly looking for a product, checking availability, or wanting to buy something near them.\n"
            "   - Examples: 'I need a good shirt', 'Is sugar available nearby?', 'Where can I find a facewash?', 'Looking for a phone case'.\n"
            "   - Task: Extract the single most relevant product keyword (e.g., 'shirt', 'sugar', 'facewash') into 'product_description' and set local_prod=True.\n\n"
            
            "2. 'general_chat':\n"
            "   - Choose this if the user is greeting you, asking general questions, or talking about anything unrelated to buying/searching local products.\n"
            "   - Examples: 'Hi, how are you?', 'What is the weather today?', 'What can you do?'\n"
            "   - Task: Set local_prod=False and set product_description=None.\n\n"
            
            "Strictly follow the output schema. Ensure all generated text in the response is in English."
        )
        system_message = SystemMessage(content=system_prompt)
        human_message = HumanMessage(
            content=f"User requeset {state.user_question}"
        )
        promt = ChatPromptTemplate(messages=[system_message,human_message])
        llm = ChatGroq(model=model_name,temperature=0.3)
        structured_llm = llm.with_structured_output(OutputSchema)
        chain = promt | structured_llm
        response = chain.invoke({})
        print(f"-------response: ---------- \n {response}")
        if response.local_prod:
            state.product_categry_des = response.product_description
            state.router_clarify = False
        else: 
            state.product_categry_des = 'general_chat_detected'
            state.router_clarify = True 
        return state 
    except Exception as e:
        print(f"Error while analysis requirements: \n\n {e} \n\n")
        return state 
    

def router(state:AgentState):
    if not state.router_clarify:
        return "proceed"
    else:
        return "clarify"


def clarify_requirements(state:AgentState):
    try:
        system_prompt = (
        "You are a helpful and polite Assistant for a hyperlocal e-commerce platform.\n"
        "Your core strength is finding the exact product the user wants from nearby shops within a 5km radius, "
        "comparing prices, and providing store locations.\n\n"
        
        "CONTEXT FOR THIS TASK:\n"
        "The user wants to find or buy something, but their request is too vague, incomplete, or missing a specific product name. "
        "You cannot query the database without knowing exactly what product they need.\n\n"
        
        "YOUR MISSION:\n"
        "Generate a friendly guidance/clarification message in English. The message must:\n"
        "1. Acknowledge that you want to help them find items within 5km, compare prices, and show shop locations.\n"
        "2. Politely ask them to clarify or specify the exact product name, brand, or category they are looking for.\n"
        "3. Keep the tone conversational, helpful, and enthusiastic (you can use words like 'bro' or 'brother' to keep it friendly if appropriate, but keep it professional too).\n\n"
        
        "Example Response Idea: 'I can help you find the best prices and store locations within 5km, brother! But could you please tell me exactly what product or item you are looking for?'\n"
        "Write ONLY the direct message to the user. Do not include any meta-text, quotes, or explanations."
        )
        system_message = SystemMessage(content=system_prompt)
        human_message = HumanMessage(content=f"""
        The user's original request is: "{state.user_question}"
        The system couldn't determine:
        - For specific product.
        Create a guidance message for the user.
        """) 
        promt = ChatPromptTemplate(messages=[system_message,human_message])
        llm = ChatGroq(model=model_name,temperature=0.7)
        chain = promt | llm | StrOutputParser()
        response = chain.invoke({})
        state.clarification_message = response
        return state 
    except Exception as e:
        print(f"find exception while in clarify_requirements nodes: {e}") 
        return state 


async def fetch_categories(state:AgentState):
    try:
        class OutputParser(BaseModel):
            category_matching : bool = True 
            product_categories_list : List[str] = []
            
        async with asyncSession() as db:
            categor_db = await fetch_categories_from_db(db) 
        category_list = [item["category"] for item in categor_db]

        print(category_list)

        system_promt = (
            "You are an intelligent Category Matching Agent for a hyperlocal e-commerce platform.\n"
            "Your job is to analyze the user's product requirement and find the best matching "
            "categories from the platform's available category list.\n\n"

            "RULES:\n"
            "1. Understand the user's intent — even if they use informal, vague, or partial words "
            "(e.g., 'facewash' → 'Beauty & Personal Care', 'shirt' → 'Clothing', 'paracetamol' → 'Medicine').\n"
            "2. Return ALL categories that could possibly contain the user's desired product.\n"
            "3. If the user's product doesn't match ANY available category, "
            "set category_matching=False and return an empty list.\n"
            "4. Never invent categories that are not in the provided list.\n"
            "5. Be generous with matching — prefer false positives over false negatives.\n\n"
            "6. Ignore uppercase of lowercase michmatch. Return in the way like Extracted product keyword."
            "OUTPUT: Respond strictly using the structured output schema provided."
        )
        system_message = SystemMessage(content=system_promt)
        human_prompt = (
            f"User's original question: \"{state.user_question}\"\n"
            f"Extracted product keyword: \"{state.product_categry_des}\"\n\n"
            f"Available categories on the platform:\n{category_list}\n\n"
            "Task: From the available categories above, return all categories that could "
            "contain or relate to the user's desired product. "
            "If nothing matches, set category_matching=False."
        )
        human_message = HumanMessage(content=human_prompt)
        llm = ChatGroq(model=model_name,temperature=0.1)
        structured_llm = llm.with_structured_output(OutputParser)
        prompts = ChatPromptTemplate(messages=[system_message,human_message])
        chain = prompts | structured_llm
        response = chain.invoke({})
        print("=======Categories fetch from response========")
        print(response)
        print("=============================================")
        state.categories_match_or_not = response.category_matching
        state.matches_categories = response.product_categories_list
        return state
    except Exception as e: 
        print(f"Found error while fetch_categories node: \n\n {e} \n\n")
        return state


def categories_router(state:AgentState):
    if state.categories_match_or_not:
        return 'proceed' 
    else:
        return 'clarify'



async def categories_clarify(state: AgentState):
    try:
        print("--- CATEGORY CLARIFICATION NODE ---")
    
        category_list = state.matches_categories
        system_prompt = (
            "You are a helpful customer support agent for a hyperlocal e-commerce platform.\n"
            "The user searched for a product, but we do not have a matching category for it.\n"
            "Your job is to generate a polite clarification message explaining that we couldn't find a direct match.\n"
            "Show them some of our available categories and kindly ask them to try again or choose from the list."
        )
        
        human_prompt = (
            f"User's original question: \"{state.user_question}\"\n"
            f"Extracted product keyword: \"{state.product_categry_des}\"\n"
            f"Our Available categories: {category_list}\n\n"
            "Task: Draft a helpful, polite, and concise response in English asking the user for clarification."
        )
        
        llm = ChatGroq(model=model_name, temperature=0.5) 
        prompts = ChatPromptTemplate(messages=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        chain = prompts | llm
        response = await chain.ainvoke({}) 
        state.categories_clarification_message = response.content
        return state

    except Exception as e:
        print(f"Found error while categories_clarify node: \n\n {e} \n\n")
        state.categories_clarification_message = (
            "Sorry, we couldn't find any category matching your requested product. "
            "Please try searching with a different keyword or choose from our available categories."
        )
        return state


async def fetch_prod_info(state: AgentState):
    try:
        print("--- FETCH PRODUCT INFORMATION NODE ---")
        async with asyncSession() as db:
            fetch_prod_information = await local_search_llm_context(
                db=db,
                categories=state.matches_categories,
                user_lat=state.user_lat,
                user_long=state.user_long,
                radius_km=5
            )
        
        state.fetch_product_info = fetch_prod_information
        system_prompt = (
            "You are an expert Shopping Assistant for a hyperlocal e-commerce platform.\n"
            "Your job is to analyze the available products found near the user and present them "
            "in a clear, structured, and helpful manner.\n"
            "Highlight key details like store name, price, and availability/distance if provided.\n"
            "If no products are available in the context, politely inform the user that no items "
            "were found within their 5km radius."
        )
        
        human_prompt = (
            f"User's original question: \"{state.user_question}\"\n"
            f"Target product/category: \"{state.product_categry_des}\"\n\n"
            f"Available Products Context (Found within 5km):\n{fetch_prod_information}\n\n"
            "Task: Based on the products context above, write a polite and concise response to the user. "
            "List the best options available for them."
        )

        
        llm = ChatGroq(model=model_name, temperature=0.3)
        prompts = ChatPromptTemplate(messages=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        chain = prompts | llm
        response = await chain.ainvoke({})
        
        state.generated_content = response.content
        print(f"Product Info Response Generated Successfully.")
        return state

    except Exception as e:
        print(f"Found error while fetch_prod_info node: \n\n {e} \n\n")
        state.generated_content = "Sorry, I encountered an error while fetching the product details. Please try again."
        return state
   
    

# ================================== Making the node ==================================
nearby_product_finder_wkf = StateGraph(state_schema=AgentState)
ANALYZE_REQUIREMENTS = "Analyze_Requirements"
CLARIFY_REQUIREMENTS = "Clarify_Requirements"
CATEGORIES_CLARIFY = "Categories_Clarify"
FETCH_CATEGORIES = "Fetch_Categories"
FETCH_PROD_INFO = "Fetch_Prod_Info"

# add nodes:
nearby_product_finder_wkf.add_node(ANALYZE_REQUIREMENTS,analysis_requirements)
nearby_product_finder_wkf.add_node(CLARIFY_REQUIREMENTS,clarify_requirements)
nearby_product_finder_wkf.add_node(FETCH_CATEGORIES,fetch_categories)
nearby_product_finder_wkf.add_node(FETCH_PROD_INFO,fetch_prod_info)
nearby_product_finder_wkf.add_node(CATEGORIES_CLARIFY,categories_clarify)

#edges:
nearby_product_finder_wkf.set_entry_point(ANALYZE_REQUIREMENTS)

nearby_product_finder_wkf.add_conditional_edges(
    ANALYZE_REQUIREMENTS,
    router,{
        "proceed":FETCH_CATEGORIES,
        "clarify":CLARIFY_REQUIREMENTS,
    }
)

nearby_product_finder_wkf.add_edge(CLARIFY_REQUIREMENTS,END)

nearby_product_finder_wkf.add_conditional_edges(
    FETCH_CATEGORIES,
    categories_router,{
        "proceed": FETCH_PROD_INFO, 
        "clarify": CATEGORIES_CLARIFY
    }
)

nearby_product_finder_wkf.add_edge(CATEGORIES_CLARIFY,END)
nearby_product_finder_wkf.add_edge(FETCH_PROD_INFO,END)


if __name__ == "__main__":
    import asyncio 
    agnet_state = AgentState(
        user_question="Hi! i want to buy a pc. could u can help me?",
        current_user_id=1,
        user_lat = 24.7632709,
        user_long  = 89.8870121
    )
    app = nearby_product_finder_wkf.compile()
    
    # save the workflow graph:
    # grph = app.get_graph().draw_mermaid_png()
    # with open("eApp/workflows/diagram/graph_pipeline.png", "wb") as f:
    #         f.write(grph)
    # print(" Success! Your graph image has been saved as 'graph_pipeline.png'")
    final_state = asyncio.run(app.ainvoke(agnet_state))
    print(final_state)
    
    

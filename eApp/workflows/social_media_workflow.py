
import re 
import requests
import datetime
import facebook
from pydantic import Field
from typing import Optional
from bs4 import BeautifulSoup
from eApp.config import CONFIG
from dotenv import load_dotenv
from pydantic import BaseModel
from eApp.database import asyncSession
from asgiref.sync import async_to_sync
from eApp.schemas import FacebookTextPost
from eApp.routes.profile import decrypt_product_id
from typing import Literal, List, Dict, Any, Union
from langgraph.checkpoint.memory import InMemorySaver
from eApp.routes.curdOperation import single_product_info_for_llms


from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from eApp.services.social_media_service import SocialMediaService



load_dotenv()
model_name = "llama-3.1-8b-instant"
search = TavilySearch(tavily_api_key=CONFIG.TAVILY_API_KEY)



# #################### Agent State #########################
class AgentState(BaseModel):
    user_question: str 
    current_user_id : int 
    platform: str = ""
    content_type: str  = ""
    product_key : str = ""
    product_details : dict = {}
    search_results: List[str] = []
    accumulated_info: List[str] = []
    generated_content: str = ""
    media_url: str = ""
    platform_specific_requirements: dict = {}
    error_messages: List[str] = []
    current_step: str = ""
    requirements_clear: bool = True  
    clarification_message: str = ""  
    final_result: Union[Dict[str, Any], str] = ""
    
    

# #################### Platform-Specific Configurations ####################
PLATFORM_CONFIGS = {
    "facebook": {
        "max_length": 5000,
        "hashtag_style": "broad",
        "call_to_action": True,
        "tone": "conversational"
    },
    "instagram": {
        "max_length": 2200,
        "hashtag_style": "trendy",
        "call_to_action": True,
        "tone": "visual_focused"
    },
    "linkedin": {
        "max_length": 3000,
        "hashtag_style": "professional",
        "call_to_action": False,
        "tone": "professional"
    }
}

# #################### Node Definitions ####################

def analyze_requirements(state: AgentState) -> AgentState:
    """Analyze user requirements and set platform/content type"""
    try:
        class Requirements(BaseModel):
            platform: Literal["facebook", "instagram", "linkedin", "unknown"]
            content_type: Literal["text", "image", "video", "unknown"]
            # Optional[str] এর জায়গায় সরাসরি str দিয়ে default ফাঁকা স্ট্রিং দেওয়া Groq এর জন্য বেশি স্ট্যাবল
            product_key: str = Field(
                default="", 
                description="The dynamic product branding code starting with 'Galacti_' if mentioned, else empty string"
            )

        system_message = SystemMessage(content="""
        Analyze the user's request to determine:
        1. Which platform they want to post on (facebook, instagram, linkedin)
        2. What type of content they want (text, image, video)
        3. Identify if there is any unique Product Branding Code starting with 'Galacti_'.
        
        IMPORTANT RULES:
        - ONLY select a platform and content_type if they are EXPLICITLY mentioned in the request.
        - If the platform is not clearly specified, return 'unknown' for platform.
        - If the content_type is not clearly specified, return 'unknown' for content_type.
        - Do NOT assume or guess defaults. Be strict: no mention means 'unknown'.
        
        PRODUCT KEY RULES:
        - Carefully look for any code that starts exactly with 'Galacti_'.
        - If you find it, extract the FULL code (e.g., 'Galacti_wQdQ5d80') and set it in 'product_key'.
        - If NO code starting with 'Galacti_' is mentioned, return an empty string "" for 'product_key'.
        
        You must respond strictly in JSON format matching the schema.
        """)
        
        human_message = HumanMessage(content=f"User request: {state.user_question}")
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name, temperature=0.0) # Temperature 0 করলে সলিড জেসন দেয় ভাই
        
        # 💡 Groq এর জন্য json_mode মেথড ব্যবহার করা সবচেয়ে নিরাপদ ও স্টেবল
        structured_llm = llm.with_structured_output(Requirements, method="json_mode")
        chain = prompt | structured_llm
        response = chain.invoke({})
        
        print(f"-------response: \n {response} \n----------")
        
        # স্টেট আপডেট লজিক
        state.product_key = response.product_key if response.product_key else ""
        state.platform = response.platform if response.platform != 'unknown' else ""
        state.content_type = response.content_type if response.content_type != 'unknown' else ""
        
        if state.platform:
            state.platform_specific_requirements = PLATFORM_CONFIGS.get(state.platform, {})
            
        state.current_step = "requirements_analyzed"
        
        # 💡 মেইন লজিক পার্ট: LLM যদি প্ল্যাটফর্ম আর কন্টেন্ট টাইপ সাকসেসফুলি বের করতে পারে, 
        # তবে রেগুলার এক্সপ্রেশনের ওপর নির্ভর না করে সরাসরি True করে দেওয়া নিরাপদ।
        if state.platform and state.content_type:
            state.requirements_clear = True
        else:
            state.requirements_clear = _are_requirements_explicit(state.user_question)
            
        return state
        
    except Exception as e:
        state.requirements_clear = False
        state.error_messages.append(f"Requirements analysis failed: {str(e)}")
        user_lower = state.user_question.lower()
        if "facebook" in user_lower or "fb" in user_lower:
            state.platform = "facebook"
        if "text" in user_lower:
            state.content_type = "text"
            
        match = re.search(r'(Galacti_\w+)', state.user_question)
        if match:
            state.product_key = match.group(1)
            state.requirements_clear = True
        return state

def _are_requirements_explicit(user_question: str) -> bool:
    """Check if user explicitly mentioned platform and content type"""
    user_lower = user_question.lower()
    
    # Platform patterns - more flexible matching
    platform_patterns = [
        r"face.?book", r"fb", r"insta", r"ig", r"linked.?in", 
        r"social.?media", r"post to", r"share on"
    ]
    
    # Content type patterns  
    content_patterns = [
        r"text", r"image", r"photo", r"picture", r"video", 
        r"only text", r"text only", r"just text"
    ]
    
    
    # Check if any platform pattern matches
    platform_mentioned = any(re.search(pattern, user_lower) for pattern in platform_patterns)
    
    # Check if any content type pattern matches
    content_mentioned = any(re.search(pattern, user_lower) for pattern in content_patterns)
    
    return platform_mentioned and content_mentioned


# #################### Failed - Clarify Requirements ####################
def clarify_requirements(state: AgentState) -> AgentState:
    """Provide a short, bulleted guidance message to the user when requirements are missing."""
    try:
        system_message = SystemMessage(content="""
        You are a friendly and precise AI Assistant for a social media and product branding tool.
        The user's previous request was missing crucial information (Platform, Content Type, or Product Code).
        
        Create a VERY SHORT, crisp, and clean response (maximum 4-5 bullet points) that tells the user exactly how to fix their prompt.
        
        CRITICAL INSTRUCTIONS:
        - Do NOT write long paragraphs. Keep it extremely concise so the user can read it in 5 seconds.
        - Mention that they can use a Product Branding Code (starting with 'Galacti_') if they want to post about a specific product.
        - Provide 2 very clean examples using 'Galacti_'.
        - Use emojis to make it look modern and visually scannable.
        """)
        
        human_message = HumanMessage(content=f"""
        The user's original request was: "{state.user_question}"
        
        The system failed to detect:
        - Social media platform (facebook, instagram, linkedin)
        - Content type (text, image, video)
        - Product Branding Code (Optional, e.g., Galacti_wQdQ5d80)
        
        Generate a super concise, bulleted guidance message in English.
        """)
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name, temperature=0.5)
        chain = prompt | llm | StrOutputParser()
        
        guidance_message = chain.invoke({})
        state.clarification_message = guidance_message
        state.current_step = "clarification_provided"
        
        print("=" * 50)
        print("🆘 CONCISE GUIDANCE MESSAGE FOR USER:")
        print("=" * 50)
        print(guidance_message)
        print("=" * 50)
        return state
        
    except Exception as e:
        state.clarification_message = """
        🤖 **I need a bit more detail to help you!**

        Please make sure your request includes:
        • **Platform:** Facebook, Instagram, or LinkedIn
        • **Content Type:** Text, Image, or Video
        • **Product Code (Optional):** Copy your `Galacti_XXXXXXXX` code from your profile.

        **💡 Quick Examples:**
        • *"Post an image on Facebook for Galacti_wQdQ5d80"*
        • *"Create a LinkedIn text post about summer tech sale"*

        Try again with a clearer format! 🚀
        """
        state.current_step = "clarification_provided"
        return state
    
# #################### Conditional Edge Function ####################
def check_requirements(state: AgentState) -> str:
    """Check if requirements are clear enough to proceed"""
    valid_platforms = ["facebook", "instagram", "linkedin"]
    valid_content_types = ["text", "image", "video"]
    
    if (state.platform in valid_platforms and 
        state.content_type in valid_content_types):
        return "proceed"
    else:
        return "clarify"


# ################## Fetch Product Informtion from product key ######################
async def fetch_product_info(state: AgentState) -> AgentState:
    try:
        if not state.product_key:
            raise ValueError("No product key found in state")
            
        product_id = decrypt_product_id(state.product_key)
        
        async with asyncSession() as db:
            product_details = await single_product_info_for_llms(db, product_id) 
            
        state.product_details = product_details
        state.current_step = "product_fetched_successfully"
        
    except Exception as e:
        state.product_details = None
        state.current_step = "product_fetch_failed"
        state.error_messages.append(f"Product Not Found: {str(e)}")
    return state


def fetch_product_router(state: AgentState) -> str:
    if state.product_details and state.current_step == "product_fetched_successfully":
        return "generate_content"  
    else:
        return "clarify_requirements"


def fetch_product_failed_clarification(state: AgentState) -> AgentState:
    state.clarification_message = """
   **Product Branding Code Invalid!**
    The code you provided (`{}`) could not be found in our system.
    • Please double-check the code from your **Profile > Manage Product**.
    • Make sure it starts exactly with `Galacti_`.
    Try again with a valid code!
    """.format(state.product_key if state.product_key else "Unknown")
    
    state.current_step = "clarification_provided"
    return state

# ==================== Get Information:) From Web Search   =============================

def research_content(state: AgentState) -> AgentState:
    """Research content based on user request - CLEANED VERSION"""
    try:
        # Generate search query
        current_date = datetime.datetime.now().strftime("%B %d, %Y") 
        system_message = SystemMessage(content="""
        You are an expert at generating a single, concise Google search query. Your goal is to create the most effective query possible to find text-based articles and blog posts. Follow these rules:
        1.  **Identify the core topic and key entities** from the user's question.
        2.  **Focus on finding recent articles or posts.** If the user asks for information on a current event or a topic where recency is important, ensure the query is optimized to return the latest results.
        3.  **Automatically exclude document formats and irrelevant sites.** Append `-filetype:pdf -filetype:doc -filetype:ppt -site:youtube.com -site:pinterest.com` to the query.
        4.  **Use specific phrases and keywords** from the user's query to ensure accuracy.
        5.  **Be concise.** The final search query should be a single string, under 50 characters, unless more detail is absolutely necessary.
        6.  **Output only the final search query string.** Do not add any extra text, explanations, or formatting.
        """)
        human_message = HumanMessage(content=f"""
        User request: {state.user_question}
        Platform: {state.platform}
        Content type: {state.content_type}
        Today Date: {current_date}
        
        Create a search query that will find current, engaging information.
        """)
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        chain = prompt | llm | StrOutputParser()
        search_query = chain.invoke({})
        
        # Perform search
        results = search.invoke(search_query)
        state.search_results = [str(results)]
        
        # Extract key information
        if "results" in results:
            for result in results["results"][:3]: 
                try:
                    # Get page content for the most relevant result
                    if result.get("url"):
                        response = requests.get(result["url"], timeout=10)
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # **CLEAN CONTENT EXTRACTION** 
                        clean_content = extract_clean_content(soup, result['url'])
                        
                        if clean_content:
                            state.accumulated_info.append(clean_content)
                        else:
                            # Fallback: basic cleaning if main extraction fails
                            basic_text = soup.get_text()
                            clean_basic = clean_extracted_text(basic_text)
                            state.accumulated_info.append(f"From {result['url']}: {clean_basic}")
                            
                except Exception as e:
                    print(f"Could not fetch {result.get('url')}: {str(e)}")
        
        state.current_step = "research_completed"
        return state
        
    except Exception as e:
        state.error_messages.append(f"Research failed: {str(e)}")
        return state


def extract_clean_content(soup, url):
    """Extract clean, relevant content from webpage"""
    
    # Strategy 1: Try to find main article content
    article_selectors = [
        'article',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.story-content',
        'main',
        '[role="main"]',
        '.main-content',
        '.content-area',
        '#content'
    ]
    
    content = None
    for selector in article_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            content = content_elem.get_text()
            break
    
    # Strategy 2: If no article found, try to get the body and clean it
    if not content:
        # Remove unwanted elements first
        for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'meta']):
            unwanted.decompose()
        
        body = soup.find('body')
        if body:
            content = body.get_text()
    
    # Clean the extracted content
    if content:
        return clean_extracted_text(content, url)
    
    return None

def clean_extracted_text(text, url=None):
    """Clean and normalize extracted text"""
    import re
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)  
    text = re.sub(r'[ \t]+', ' ', text)       
    
    # Remove common unwanted patterns
    unwanted_patterns = [
        r'Skip to main content',
        r'Sign up today to receive premium content!',
        r'Sign Up',
        r'Become an Insider',
        r'Menu',
        r'Log in',
        r'Search',
        r'Twitter',
        r'Facebook',
        r'LinkedIn',
        r'Subscribe',
        r'Follow us',
        r'Related articles',
        r'Recommended for you',
        r'Read more',
        r'\.{3,}',  # Multiple dots
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Split into lines and clean each line
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Keep only substantial lines (more than 20 chars typically contain real content)
        if len(line) > 20 and not line.startswith(('©', '©', 'Privacy', 'Terms')):
            cleaned_lines.append(line)
    
    # Join back with reasonable spacing
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Final cleanup
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # Max 2 consecutive newlines
    
    # Add source reference
    if url:
        cleaned_text = f"Source: {url}\n\n{cleaned_text}"
    
    # Limit length while preserving complete sentences if possible
    if len(cleaned_text) > 3000:
        # Try to truncate at sentence boundary
        truncated = cleaned_text[:3000]
        last_period = truncated.rfind('.')
        if last_period > 2500:  # Only if we have a reasonable cutoff point
            cleaned_text = truncated[:last_period + 1]
        else:
            cleaned_text = truncated + "... [content truncated]"
    return cleaned_text.strip()



# ==================== Generate Promt If we need to generate Image/video  =============================
def generate_media(state: AgentState) -> AgentState:
    print("<--------Generating Content--------->")
    """Generate media content (image/video) if requested"""
    if state.content_type == "text":
        return state
        
    try:
        # In production, you would integrate with:
        # - DALL-E/Stable Diffusion for images
        # - RunwayML/Pika Labs for videos
        # - Or any other media generation service
        ip_address = "103.133.254.2:6085"
        if state.content_type == "image":
           all_product =  state.product_details.get('Product Information')
           file_name = all_product.get('product_image')
           if file_name:
            final_url = f"http://{ip_address}/images/${file_name}"
        state.media_url = final_url
        state.current_step = "media_generated"
        print("media_url generated: \n {}".format(final_url))
        return state
    except Exception as e:
        state.error_messages.append(f"Media generation failed: {str(e)}")
        return state
    
    
    
# ========================== Create Social Media Post  ===============================
def create_social_media_content(state: AgentState) -> AgentState:
    """Create platform-optimized social media content - TOPIC AWARE VERSION"""
    print("<----Platfrom Specific Post----------->")
    try:
        platform_config = state.platform_specific_requirements
        
        system_message = SystemMessage(content=f"""
        You are a professional social media content creator for {state.platform}.
        
        YOUR JOB: Create engaging social media content about WHATEVER TOPIC the user requests.
        
        Platform Requirements:
        - Max length: {platform_config['max_length']} characters  
        - Hashtag style: {platform_config['hashtag_style']}
        - Tone: {platform_config['tone']}
        - Call to action: {platform_config['call_to_action']}
        
        RULES:
        1. Create content about EXACTLY what the user asks for
        2. Use the research information to make it accurate 
        3. Make it engaging and platform-appropriate
        4. Include relevant hashtags for THAT SPECIFIC TOPIC
        5. No image/video placeholders
        6. No event registrations or specific dates
        
        Be creative but stay on-topic!
        """)
        
        human_message = HumanMessage(content=f"""
        CREATE A {state.platform.upper()} POST ABOUT THIS TOPIC:
        "{state.user_question}"
        
        RESEARCH INFORMATION:
        {state.accumulated_info}
        
        CONTEXT:
        - Platform: {state.platform}
        - Content type: {state.content_type}
        - Call to action needed: {platform_config['call_to_action']}
        
        CREATE CONTENT THAT:
        - Is about "{state.user_question}"
        - Uses the research to be accurate
        - Is engaging for {state.platform} users
        - Has relevant hashtags for this topic
        - Encourages interaction if needed
        
        Return only the final post text.
        """)
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        chain = prompt | llm | StrOutputParser()
        
        content = chain.invoke({})
        
        print("<-----------------Generated content--------------------->")
        print(content)
        state.generated_content = content
        state.current_step = "content_created"
        
        print(f"Topic: {state.user_question}")
        print(f"Platform: {state.platform}")
        print(f"Content length: {len(content)}")
        return state
        
    except Exception as e:
        state.error_messages.append(f"Content creation failed: {str(e)}")
        return state
    
    
# ===================== Posting on social media =======================

def post_to_social_media(state: AgentState) -> AgentState:
    """Post content to the appropriate social media platform"""
    print("<------ Posting in social media Node --->")
    try:
        
        # ============== FACEBOOK PLATFORM LOGIC ==============
        if state.platform == "facebook":
            print("<--- posting on facebook --->")
            if state.content_type == "text":
                print(f"<--- posting on facebook ---- {state.content_type}--->")
                result = async_to_sync(SocialMediaService.post_to_facebook_text)(
                    user_id=int(state.current_user_id),
                    content=str(state.generated_content)
                )
                state.final_result = result
                print("--------------------------")
                print("Facebook Post Result:")
                print(f"{result}")
                print("--------------------------")
                
            elif state.content_type == "image":
                result = async_to_sync(SocialMediaService.post_to_facebook_photo)(
                    user_id=int(state.current_user_id),
                    content=str(state.generated_content),
                    photo_path=state.media_url
                )
                state.final_result = result
                
            elif state.content_type == "video":
                result = async_to_sync(SocialMediaService.post_to_facebook_video)(
                    user_id=int(state.current_user_id),
                    content=str(state.generated_content),
                    video_path=state.media_url
                )
                state.final_result = result
                
            print(f"Facebook posting result: {result}")
            
        # ================= INSTAGRAM PLATFORM LOGIC ================
        elif state.platform == "instagram":
            print("Instagram posting would happen here")
            # TODO: Implement Instagram posting service
            
        # ================= LINKEDIN PLATFORM LOGIC ==================
        elif state.platform == "linkedin":
            print("LinkedIn posting would happen here")
            # TODO: Implement LinkedIn posting service
            
        state.current_step = "posted"
        return state
        
    except Exception as e:
        print("----------------------------------------------------------------------------------")
        print(f"Posting failed: {str(e)}")
        print("----------------------------------------------------------------------------------")
        state.error_messages.append(f"Posting failed: {str(e)}")
        return state
    
    

def quality_check(state: AgentState) -> AgentState:
    """Final quality check before posting"""
    try:
        system_message = SystemMessage(content="""
        Review the generated content for:
        1. Platform appropriateness
        2. Engagement potential
        3. Error-free writing
        4. Hashtag relevance
        
        Return 'approved' or 'needs_revision' with brief feedback.
        """)
        
        human_message = HumanMessage(content=f"""
        Platform: {state.platform}
        Content Type: {state.content_type}
        Generated Content: {state.generated_content}
        """)
        
        class QualityCheck(BaseModel):
            status: Literal["approved", "needs_revision"]
            feedback: str = ""
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        structured_llm = llm.with_structured_output(QualityCheck)
        chain = prompt | structured_llm
        
        result = chain.invoke({})
        print(f"<-----------\n {result} --------------->")
        if result.status == "needs_revision":
            print(f"Quality check feedback: {result.feedback}")
            
        state.current_step = "quality_checked"
        return state
        
    except Exception as e:
        state.error_messages.append(f"Quality check failed: {str(e)}")
        return state


# =============================== final evalution status: ====================================
def final_evalution_state(state:AgentState):
    try: 
        system_message = SystemMessage(content="""
        You are a helpful assistant that give final instruction base on previous response to users.
        If everything is okay then give greet to the user on the other hand if user's previous request was 
        unclear about which platform or content type they want.
        Create a friendly, helpful message that:
        1. Explains what went wrong
        2. Provides clear examples of how to format requests
        3. Explains what this tool can do
        4. Encourages the user to try again with better formatting
        
        Keep the message concise and helpful.
        """)
        
        human_message = HumanMessage(content=f"""
        The user's original request was: "{state.user_question}"
        The previous state is : "{state.final_result}
        """)
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        chain = prompt | llm 
        result = chain.invoke({})
        return state
    except Exception as e:
        print(f"exection while evaluating final_evalution_status: {e}")




# #################### Build the Graph ####################

social_media_wkf = StateGraph(state_schema=AgentState)

ANALYZE_REQUIREMENTS = "Analyze_Requirements"
CLARIFY_REQUIREMENTS = "Clarify_Requirements"
RESEARCH_CONTENT = "Research_Content"
GENERATE_MEDIA = "Generate_Media"
CREATE_CONTENT = "Create_Content"
QUALITY_CHECK = "Quality_Check"
POST_CONTENT = "Post_Content"
FINAL_USER_RESULT = "Final_User_Reust"
FETCH_PRODUCT_INFO = "Fetch_Product_Info"
FETCH_PRODUCT_FAILED_CLARIFICATION = "Fetch_Product_Failed"

# Add nodes
social_media_wkf.add_node(ANALYZE_REQUIREMENTS, analyze_requirements)
social_media_wkf.add_node(CLARIFY_REQUIREMENTS, clarify_requirements) 
social_media_wkf.add_node(RESEARCH_CONTENT, research_content)
social_media_wkf.add_node(GENERATE_MEDIA, generate_media)
social_media_wkf.add_node(CREATE_CONTENT, create_social_media_content)
social_media_wkf.add_node(QUALITY_CHECK, quality_check)
social_media_wkf.add_node(POST_CONTENT, post_to_social_media)
social_media_wkf.add_node(FINAL_USER_RESULT,final_evalution_state)
social_media_wkf.add_node(FETCH_PRODUCT_INFO,fetch_product_info)
social_media_wkf.add_node(FETCH_PRODUCT_FAILED_CLARIFICATION,fetch_product_failed_clarification)

    
# Define social_media with conditional edge
social_media_wkf.set_entry_point(ANALYZE_REQUIREMENTS)

# Conditional edge after analyze_requirements
social_media_wkf.add_conditional_edges(
    ANALYZE_REQUIREMENTS,
    check_requirements,
    {
        "proceed": FETCH_PRODUCT_INFO,     
        "clarify": CLARIFY_REQUIREMENTS 
    }
)

# Rest of the edges
social_media_wkf.add_edge(CLARIFY_REQUIREMENTS, END) 

social_media_wkf.add_conditional_edges(
    FETCH_PRODUCT_INFO,
    fetch_product_router,{
        "generate_content": RESEARCH_CONTENT,
        "clarify_requirements": FETCH_PRODUCT_FAILED_CLARIFICATION
    }

)
social_media_wkf.add_edge(FETCH_PRODUCT_FAILED_CLARIFICATION,END)
social_media_wkf.add_edge(RESEARCH_CONTENT, GENERATE_MEDIA)
social_media_wkf.add_edge(GENERATE_MEDIA, CREATE_CONTENT)
social_media_wkf.add_edge(CREATE_CONTENT, QUALITY_CHECK)
social_media_wkf.add_edge(QUALITY_CHECK, POST_CONTENT)
social_media_wkf.add_edge(POST_CONTENT,FINAL_USER_RESULT)
social_media_wkf.add_edge(FINAL_USER_RESULT, END)


# =================== Check the the workflow ===================
if __name__ == "__main__":
    import asyncio 
    memory = InMemorySaver()
    agnet_state = AgentState(
        user_question = "i want to this product: Galacti_wQdQ5d80 on facebook and i want to post only text",
        current_user_id  = 1  
    )
    app = social_media_wkf.compile(memory)
    # save the workflow graph:
    # grph = app.get_graph().draw_mermaid_png()
    # with open("eApp/workflows/diagram/graph_social_media.png", "wb") as f:
    #         f.write(grph)
    # print(" Success! Your graph image has been saved as 'graph_social_media.png'")
    config = {"configurable": {"thread_id": "test_thread_123"}}
    print(asyncio.run(app.ainvoke(agnet_state,config=config)))
    

import re 
import requests
import datetime
import facebook
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel
from asgiref.sync import async_to_sync
from eApp.schemas import FacebookTextPost
from typing import Literal, List, Dict, Any, Union



from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from eApp.services.social_media_service import SocialMediaService



load_dotenv()
model_name = "llama-3.1-8b-instant"
search = TavilySearch()



# #################### Agent State #########################
class AgentState(BaseModel):
    user_question: str 
    current_user_id : int 
    platform: str = ""
    content_type: str  = ""
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
        system_message = SystemMessage(content="""
        Analyze the user's request to determine:
        1. Which platform they want to post on (facebook, instagram, linkedin)
        2. What type of content they want (text, image, video)
        
        IMPORTANT RULES:
        - ONLY select a platform and content_type if they are EXPLICITLY mentioned in the request.
        - If the platform is not clearly specified, return 'unknown' for platform.
        - If the content_type is not clearly specified, return 'unknown' for content_type.
        - Do NOT assume or guess defaults. Be strict: no mention means 'unknown'.
        - Examples:
          - If request says "post on facebook with image", then platform='facebook', content_type='image'
          - If request is "kire vai kmn asos re tui", no platform or type mentioned, so platform='unknown', content_type='unknown'
        
        Return JSON with platform and content_type fields.
        """)
        
        human_message = HumanMessage(content=f"User request: {state.user_question}")
        
        class Requirements(BaseModel):
            platform: Literal["facebook", "instagram", "linkedin", "unknown"]
            content_type: Literal["text", "image", "video", "unknown"]
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        structured_llm = llm.with_structured_output(Requirements)
        chain = prompt | structured_llm
        response = chain.invoke({})
        print(f"-------response: {response}----------")
        
        # Set only if not 'unknown'
        state.platform = response.platform if response.platform != 'unknown' else ""
        state.content_type = response.content_type if response.content_type != 'unknown' else ""
        if state.platform:
            state.platform_specific_requirements = PLATFORM_CONFIGS.get(state.platform, {})
        state.current_step = "requirements_analyzed"
        
        state.requirements_clear = _are_requirements_explicit(state.user_question)
    
        print(f"Platform: {state.platform}, Content Type: {state.content_type}")
        print(f"Requirements clear: {state.requirements_clear}")
        return state
        
    except Exception as e:
        state.requirements_clear = False
        state.error_messages.append(f"Requirements analysis failed: {str(e)}")
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
    """Provide guidance to user when requirements are unclear"""
    try:
        system_message = SystemMessage(content="""
        You are a helpful assistant that guides users on how to use this social media automation tool.
        The user's previous request was unclear about which platform or content type they want.
        
        Create a friendly, helpful message that:
        1. Explains what went wrong
        2. Provides clear examples of how to format requests
        3. Explains what this tool can do
        4. Encourages the user to try again with better formatting
        
        Keep the message concise and helpful.
        """)
        
        human_message = HumanMessage(content=f"""
        The user's original request was: "{state.user_question}"
        
        The system couldn't determine:
        - Which social media platform (facebook, instagram, linkedin)
        - What type of content (text, image, video)
        
        Create a guidance message for the user.
        """)
        
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        llm = ChatGroq(model=model_name)
        chain = prompt | llm | StrOutputParser()
        
        guidance_message = chain.invoke({})
        
        state.clarification_message = guidance_message
        state.current_step = "clarification_provided"
        
        print("=" * 50)
        print("🆘 GUIDANCE MESSAGE FOR USER:")
        print("=" * 50)
        print(guidance_message)
        print("=" * 50)
        
        return state
        
    except Exception as e:
        # Fallback message if LLM fails
        state.clarification_message = """
🤖 **How to Use This Social Media Automation Tool**

I couldn't understand your request clearly. Here's how to get the best results:

**Please specify in your request:**
- **Which platform**: Facebook, Instagram, or LinkedIn
- **What content type**: Text, Image, or Video  
- **Your topic**: What you want to post about

**Example formats:**
- "Create a Facebook post with image about AI in healthcare"
- "Make an Instagram text post about healthy eating tips"  
- "Generate LinkedIn video content about career growth"
- "Facebook post about Bangladesh cricket team with image"


**What I can do for you:**
- Research your topic automatically
- Create engaging social media content  
- Generate images/videos (if requested)
- Post directly to your social media

Try again with a clearer request! 
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
        
        if state.content_type == "image":
            # Generate image prompt based on research
            image_prompt_system = SystemMessage(content="Create a detailed image generation prompt")
            image_prompt_human = HumanMessage(content=f"""
            Based on this research: {state.accumulated_info}
            Create an image prompt for social media that matches this request: {state.user_question}
            """)
            
            prompt = ChatPromptTemplate.from_messages([image_prompt_system, image_prompt_human])
            llm = ChatGroq(model=model_name)
            chain = prompt | llm | StrOutputParser()
            image_prompt = chain.invoke({})
            
            # Here you would call your image generation API
            # For now, we'll simulate it
            state.media_url = f"generated_images/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            print(f"Image prompt: {image_prompt}")
            
        elif state.content_type == "video":
            # Similar approach for video
            state.media_url = f"generated_videos/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            
        state.current_step = "media_generated"
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

workflow = StateGraph(state_schema=AgentState)

ANALYZE_REQUIREMENTS = "Analyze_Requirements"
CLARIFY_REQUIREMENTS = "Clarify_Requirements"
RESEARCH_CONTENT = "Research_Content"
GENERATE_MEDIA = "Generate_Media"
CREATE_CONTENT = "Create_Content"
QUALITY_CHECK = "Quality_Check"
POST_CONTENT = "Post_Content"
FINAL_USER_RESULT = "Final_User_Reust"

# Add nodes
workflow.add_node(ANALYZE_REQUIREMENTS, analyze_requirements)
workflow.add_node(CLARIFY_REQUIREMENTS, clarify_requirements) 
workflow.add_node(RESEARCH_CONTENT, research_content)
workflow.add_node(GENERATE_MEDIA, generate_media)
workflow.add_node(CREATE_CONTENT, create_social_media_content)
workflow.add_node(QUALITY_CHECK, quality_check)
workflow.add_node(POST_CONTENT, post_to_social_media)
workflow.add_node(FINAL_USER_RESULT,final_evalution_state)
    
# Define workflow with conditional edge
workflow.set_entry_point(ANALYZE_REQUIREMENTS)

# Conditional edge after analyze_requirements
workflow.add_conditional_edges(
    ANALYZE_REQUIREMENTS,
    check_requirements,
    {
        "proceed": RESEARCH_CONTENT,     
        "clarify": CLARIFY_REQUIREMENTS 
    }
)

# Rest of the edges
workflow.add_edge(CLARIFY_REQUIREMENTS, END) 
workflow.add_edge(RESEARCH_CONTENT, GENERATE_MEDIA)
workflow.add_edge(GENERATE_MEDIA, CREATE_CONTENT)
workflow.add_edge(CREATE_CONTENT, QUALITY_CHECK)
workflow.add_edge(QUALITY_CHECK, POST_CONTENT)
workflow.add_edge(POST_CONTENT,FINAL_USER_RESULT)
workflow.add_edge(FINAL_USER_RESULT, END)

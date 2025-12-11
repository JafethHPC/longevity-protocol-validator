import base64
from io import BytesIO
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings

vision_llm = ChatOpenAI(
    model="gpt-4o", 
    max_tokens=1024,
    api_key=settings.OPENAI_API_KEY
)

def encode_image(image: Image.Image) -> str:
    """
    Convert a PIL Image to a base64 string for OpenAI.
    """
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def analyze_chart(image: Image.Image) -> str:
    """
    Uses GPT-4o Vision to describe a scientific figure.
    """
    base64_image = encode_image(image)

    prompt = """
    You are an expert Biologist analyzing a figure from a scientific paper.
    Describe this image in detail.
    1. What is the type of chart? (Bar, Line, Kaplan-Meier, etc.)
    2. What are the axes labels?
    3. What is the key trend or data point shown?
    4. What is the scientific conclusion of this figure?

    Format the output as a concise paragraph suitable for searching.
    """

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    )

    print("Looking at figure...")
    response = vision_llm.invoke([message])
    return response.content
import os
import time

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("API_GEMINI"))
model = genai.GenerativeModel("gemini-1.5-flash")

def moderate_content_with_ai(text):
    """
    Checks the provided text for inappropriate or harmful content using an AI model.

    The function sends the text to an AI model for moderation, looking for categories of harmful
    content (e.g., harassment, hate speech, explicit content). If harmful content is detected with
    a certain probability threshold, the content is flagged as inappropriate.

    Args:
        text (str): The text to be analyzed for inappropriate content.

    Returns:
        tuple: A tuple (bool, str) where:
            - bool indicates if the content is blocked (True if inappropriate content is found).
            - str provides the reason or category for blocking, or an empty string if no issues.

    Notes:
        - The function will retry up to 3 times in case of issues with the AI service.
        - If the AI service is unavailable after retries, the content is automatically blocked.
    """
    response = None
    safety_categories = {
        7: "HARM_CATEGORY_HARASSMENT",
        8: "HARM_CATEGORY_HATE_SPEECH",
        9: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        10: "HARM_CATEGORY_DANGEROUS_CONTENT"
    }
    text_proc = f'Please check the following text for obscene language and insults: "{text}"'

    count = 0
    while count <= 3 and not response:
        count += 1
        try:
            response = model.generate_content(text_proc)
        except Exception as e:  # I don't know what type of error can be received from the AI-service
            print("Error while AI text proceeds: ", str(e))
            time.sleep(5)

    if not response:
        print("Content has been blocked because of AI-moderation is not available")
        return True, "Error while AI text proceeds"
    else:
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                for rating in candidate.safety_ratings:
                    category_name = safety_categories.get(rating.category, "UNKNOWN_CATEGORY")
                    if rating.probability >= 2:
                        return True, category_name

                return False, ""
        else:
            return False, ""



def generate_relevant_reply(post, comment):
    """
    Generates a relevant response to a comment based on the content of the associated post.

    This function uses an AI model to generate a response to a comment, considering the content of the
    original post. The AI model generates a reply that is relevant to the context of the post and comment.

    Args:
        post (Post): The Post instance containing the original content that the comment is associated with.
        comment (Comment): The Comment instance containing the user's comment to which a reply is to be generated.

    Returns:
        str: The AI-generated reply to the comment based on the post content.

    Notes:
        - The function creates a prompt using both the post content and the comment content and passes it to
          the AI model for response generation.
        - If the model encounters issues or returns an invalid result, handling for such scenarios may be needed.
    """

    prompt = f"Generate a relevant response to this comment: '{comment.content}' based on the post: '{post.content}'"
    reply = model.generate_content(prompt)

    return reply.text

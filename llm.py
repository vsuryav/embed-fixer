import os
import google.generativeai as genai


async def summarize_messages(username: str, messages: list[str]) -> str:
    """Summarize a user's recent messages using Gemini 1.5 Flash API."""

    api_key = os.environ.get("gemini_api_key")

    if not api_key:
        return "Error: gemini_api_key environment variable is not set."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        formatted_messages = "\n".join(f"- {msg}" for msg in messages)

        prompt = (
            f"Summarize what the Discord user '{username}' has been saying "
            f"based on their recent messages below.\n\n"
            f"{formatted_messages}\n\n"
            f"Format your response as bullet points only. No introduction or conclusion."
        )

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

        return "Could not generate a summary. Please try again."

    except Exception as e:
        error_msg = str(e).lower()
        if "api_key" in error_msg or "invalid" in error_msg:
            return "Error: Invalid or missing gemini_api_key."
        if "quota" in error_msg:
            return "Error: Gemini API quota exceeded."
        return "An error occurred while generating the summary."
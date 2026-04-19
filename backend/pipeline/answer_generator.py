"""
Answer Generator — Generates a natural language response from GraphDB results.
"""
from google import genai
from ..config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_natural_language_answer(question: str, results: dict) -> str:
    """
    Given the user question and the JSON results from GraphDB, 
    ask the LLM to summarize the answer in natural language.
    """
    bindings = results.get("results", {}).get("bindings", [])
    
    if not bindings:
        return "I queried the database, but no data was found that matched your question. The data might not exist in the Knowledge Graph yet."
    
    # Simplify the datastructure to save tokens and prevent confusion
    simplified_data = []
    for row in bindings[:50]:  # Limit to 50 rows so prompt doesn't overload
        simplified_row = {}
        for var, val in row.items():
            value = val.get("value", "")
            # Clean up URIs
            if "https://gemr-kg.org/ontology#" in value:
                value = value.split("#")[-1]
            simplified_row[var] = value
        simplified_data.append(simplified_row)

    snippet_msg = ""
    if len(bindings) > 50:
        snippet_msg = f" (Note: taking the first 50 out of {len(bindings)} total rows)"

    prompt = f"""
You are an expert AI assistant for a macroeconomic and political risk database called GEMR-KG. 
The user asked a question, and we executed a graph database query behind the scenes to fetch the following data.

USER QUESTION: {question}

DATA RETURNED{snippet_msg}:
{simplified_data}

INSTRUCTIONS:
1. Provide a high-level, clear natural language summary that answers the user's question.
2. The user will be looking at a raw data table right below your answer. THEREFORE, DO NOT list every single data point or reproduce the table. 
3. Instead of regurgitating all the numbers, describe the BIG PICTURE: the overall trend, the highest/lowest points, or the general conclusion.
4. Keep the answer extremely plain, direct, and concise. Avoid unnecessary formatting like bold text or nested bullet points.
5. DO NOT explain the graph database, the SPARQL query, or the system pipeline. Just answer the question.
"""

    import time
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 10 * (attempt + 1)
                print(f"  [Answer Generator] API busy/rate-limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    return "I was able to retrieve the results, but the AI language model is currently experiencing high demand and couldn't generate a conversational summary."

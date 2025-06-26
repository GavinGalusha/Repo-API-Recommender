from duckduckgo_search import DDGS

def search_for_microservice(query):
    results = DDGS().text(f"open source microservice {query} github", max_results=2)
    if results:
        return f"- {results[0]['title']} ({results[0]['href']}): {results[0]['body'][:200]}..."
    return "No relevant open-source projects found."

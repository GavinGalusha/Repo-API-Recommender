from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()






def describe_java_api(api_code: str) -> str:
    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an expert software engineer who explains Java REST API code to developers. "
                "Your job is to read API method implementations and summarize their behavior clearly and concisely. "
                "Include what HTTP method is used, what the endpoint path is (if known), what data it returns, "
                "and any notable implementation or response behavior. If it's a controller class, mention that too."
            )
        },
        {
            "role": "user",
            "content": (
                "Please explain what this Java Spring REST API code is doing in simple, descriptive language:\n\n"
                f"{java_code}\n\n"
                "Include: the HTTP method, content type, response body, and controller purpose."
            )
        }
    ],
    temperature=0.3
)

    return response.choices[0].message.content



# example java code to test the function    
java_code = """
@RestController
public class WelcomeController {

    @RequestMapping(method = RequestMethod.GET, produces = {"application/json"})
    public @ResponseBody String helloWorld() {
        return "Hello FUCKING World!!!";
    }
}
"""


description = describe_java_api(java_code)
print(description)
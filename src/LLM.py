import lmstudio as lms
from encoders.GIST_large_Embedding_V0 import get_gist_embedding
from encoders.Linq_Embed_Mistral import get_linq_embedding  
from encoders.SFR_Embedding_Mistral import get_sfr_embedding


SERVER_API_HOST = "localhost:1234"

# This must be the *first* convenience API interaction (otherwise the SDK
# implicitly creates a client that accesses the default server API host)
lms.configure_default_client(SERVER_API_HOST)

model = lms.llm("ibm/granite-3.1-8b")


def describe_api(api_code):
    result = model.respond("Give clear and concise description of what the following apis do. These natural language descriptions will be used to generate embeddings, so focus on meaning and purpose, not implementation details. The output should be in a similar format to this: The provided code snippet represents a RESTful controller in Java using Spring Framework, specifically designed to handle HTTP GET requests. The purpose of this controller is to generate an HTTP response with the message 'Hello FUCKING World!!!' when accessed via a GET request. In terms of API functionality, it's essentially a simple 'hello world' service that returns a string in JSON format. It doesn't accept any input parameters and does not interact with a database or other external resources. Its main role is to demonstrate the basic structure of a Spring-based web application and serve as an entry point for further development. The @RestController annotation marks this class as a controller that handles HTTP requests and returns coherent responses, usually in JSON format. The @RequestMapping(method = RequestMethod.GET) specifies that this controller should handle GET requests, while the produces parameter ('application/json') indicates that it will return data in JSON format. Finally, the helloWorld() method is annotated with @ResponseBody to instruct Spring to directly place the returned string into the response body of the HTTP response" + api_code)
    return result


def build_Natural_Language_Description_Library(text_file):
    with open(text_file, 'r') as file:
        text = file.read()

    return




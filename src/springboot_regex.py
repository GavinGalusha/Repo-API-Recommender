import re


# regex search for spring boot packages
def get_springboot_regex(text):
    pattern = r"""
            @                   # starts with '@'
            (?P<annotation>     # capture annotation name
                Entity |
                Repository |
                Service |
                RestController
            )
            \b                  # word boundary to avoid partial matches
        """

    matches = re.finditer(pattern, text, re.VERBOSE)
    return list(matches)

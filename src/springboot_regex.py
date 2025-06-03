import re


# regex search for spring boot packages
def get_springboot_regex(text, API_only=True):
    if API_only:
        pattern = r"""
        @
        (?P<annotation>
            RestController
        )
        \b
        """

    else:
        pattern = r"""
                @
                (?P<annotation>
                    Entity |
                    Repository |
                    Service |
                    RestController
                )
                \b
                """

    matches = re.finditer(pattern, text, re.VERBOSE)
    return list(matches)

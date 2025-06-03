import re


def get_springboot_regex(text):
    entity = re.search("@Entity", text)
    repo = re.search("@Repository", text)
    service = re.search("@Service", text)
    controller = re.search("@RestController", text)

    return entity, repo, service, controller

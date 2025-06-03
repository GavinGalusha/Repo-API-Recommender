import re


def get_endpoint_regex(text):
    creates = re.search("@PostMapping", text)
    reads = re.search("@GetMapping", text)
    updates = re.search("@PutMapping", text)
    deletes = re.search("@DeleteMapping", text)

    return creates, reads, updates, deletes

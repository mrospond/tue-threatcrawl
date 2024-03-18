"""File that contains methods for detecting honeypot CAPTCHAs"""


def detect_honeypot(page: str):
    """Detect honeypot CAPTCHAs on the given `page`

    This function finds all instances of an input HTML tag and checks whether this input field is visible on screen.
    The function then returns all instances of inputs that are not visible and should thus not be used by the system.

    Parameters
    ---------
    page : str
        The page that should be checked for honeypots

    Returns
    ---------
    list of str
        List of all inputs that are hidden from view. The list may be empty.
    """
    # Output list containing the hidden input fields
    out = []

    # Split the page based on <input, and add the start of the tag at the front of every part of the split except the
    # first.
    split = page.split("<input")

    # Check in every input tag whether it should be visible or not
    for subsection in split[1:]:
        sub_split = subsection.split(">")
        if "display: none" in sub_split[0] or "visibility: hidden" in sub_split[0] or "opacity: 0" in sub_split[0] or \
                "display:none" in sub_split[0] or "visibility:hidden" in sub_split[0] or "opacity:0" in sub_split[0] or\
                "type=hidden" in sub_split[0]:
            out.append("<input" + sub_split[0] + ">")

    return out

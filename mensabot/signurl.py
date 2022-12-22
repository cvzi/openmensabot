from requests.packages.urllib3.util import parse_url
from urllib.parse import quote, unquote
import hashlib
import hmac
import base64

""" Sign and check a URL using the client_secret """
__author__ = 'christopher@levire.com, cuzi@openmail.cc'


def sign_url(input_url=None, client_id=None, client_secret=None):
    """ Sign a request URL with a Crypto Key.

        Usage:
        from urlsigner import sign_url

        signed_url = sign_url(input_url=my_url,
                              client_id=CLIENT_ID,
                              client_secret=CLIENT_SECRET)

        Args:
        input_url - The URL to sign
        client_id - Your Client ID
        client_secret - Your Crypto Key

        Returns:
        The signed request URL
    """

    # Error if any parameters aren't given
    if not input_url or not client_secret:
        raise ValueError("Expected arguments input_url and client_secret")

    # Add the Client ID to the URL
    delimeter = '&' if '?' in input_url else '?'
    if client_id:
        input_url += "%sclient=%s" % (delimeter, client_id)
        delimeter = '&'

    url = parse_url(input_url)

    # We only need to sign the path+query part of the string
    url_to_sign = url.path
    if url.query:
        url_to_sign += "?" + url.query

    # Decode the private key into its binary format
    # We need to decode the URL-encoded private key
    decoded_key = base64.urlsafe_b64decode(client_secret)

    # Create a signature using the private key and the URL-encoded
    # string using HMAC SHA1. This signature will be binary.
    signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)

    # Encode the binary signature into base64 for use within a URL
    encoded_signature = base64.urlsafe_b64encode(signature.digest())

    original_url = url.scheme + "://" + url.netloc + url.path + ("?" + url.query if url.query else '')

    # Return signed URL
    return original_url + delimeter + "signature=" + quote(encoded_signature.decode())


def check_url(input_url=None, client_secret=None):
    """ Check a signed request URL with a Crypto Key.

        Usage:
        from urlsigner import check_url

        is_valid = check_url(input_url=my_url,
                              client_secret=CLIENT_SECRET)

        Args:
        input_url - The signed URL
        client_secret - Your Crypto Key

        Returns:
        True or False
    """

    # Error if any parameters aren't given
    if not input_url or not client_secret:
        raise ValueError("Expected arguments input_url and client_secret")

    url = parse_url(input_url)

    # Extract signature
    if not url.query:
        return False

    parts = url.query.rsplit("&signature=", 1)
    if len(parts) != 2:
        parts = url.query.rsplit("signature=", 1)
        if len(parts) != 2:
            return False

    # If signature was not the last part of the url, reorder it:
    if "&" in parts[1]:
        parts[0] += "&" + parts[1].split("&", 1)[1]
        parts[1] = parts[1].split("&", 1)[0]

    query = parts[0]
    actual_signature = parts[1]

    # We only need to sign the path+query part of the string
    url_to_sign = url.path
    if query:
        url_to_sign += "?" + (query[1:] if query.startswith('&') else query)

    # Decode the private key into its binary format
    # We need to decode the URL-encoded private key
    decoded_key = base64.urlsafe_b64decode(client_secret)

    # Create a signature using the private key and the URL-encoded
    # string using HMAC SHA1. This signature will be binary.
    signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)

    # Encode the binary signature into base64 for use within a URL
    encoded_signature = base64.urlsafe_b64encode(signature.digest())

    return encoded_signature.decode() == unquote(actual_signature, errors='strict')

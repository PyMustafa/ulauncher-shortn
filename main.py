import requests 
import logging
import re
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

# Create an instance of logger at a module level
logger = logging.getLogger(__name__)

# Base URL for the is.gd URL shortening API
shortener_url = "https://is.gd"


class ShortnExtension(Extension):
    """
    The main extension class that sets up and runs the Ulauncher extension.
    """

    def __init__(self):
        # Initialize the Extension class and subscribe to the KeywordQueryEvent
        super(ShortnExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    """
    Event listener that handles keyword queries entered in Ulauncher.
    """

    # Define error messages for specific error codes returned by the is.gd API
    errors = {
        1: "Bad Request",
        2: "Not Acceptable",
        3: "Bad Gateway",
        4: "Service Unavailable",
    }

    def on_event(self, event, extension):
        """
        Handles the event triggered by a keyword query.
        Parses the query, shortens the URL, and returns appropriate results.
        """
        # Get the query string entered by the user
        query = event.get_argument() or ""

        if not query:
            # If no URL is provided, display a message to the user
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="No URL provided!",
                        description="eg. google.com | google.com stats | google.com customurl stats",
                        on_enter=HideWindowAction(),
                    )
                ]
            )

        # Split the query into parts (URL, custom URL, stats)
        query_parts = query.split()
        url = None
        custom = None
        stats = False

        # Extract the URL from the query
        if re.match(r"\w+://", query_parts[0]):
            url = query_parts[0]
        else:
            url = "http://" + query_parts[0]

        # Extract the custom URL and stats flag if provided
        if len(query_parts) > 1:
            if query_parts[1] == "stats":
                stats = True
            else:
                custom = query_parts[1]

        if len(query_parts) > 2 and query_parts[2] == "stats":
            stats = True

        # Call the URL shortener function
        response_data = self.shortn(url, custom, stats)

        if "shorturl" in response_data:
            # If successful, prepare the shortened URL and stats page
            short_url = response_data["shorturl"]
            stats_page = f"{shortener_url}/stats.php?url={str(response_data['shorturl'])[str(response_data['shorturl']).rindex('/') + 1:]}"

            # Depending on the options provided, return the appropriate result items
            if custom and stats:
                return RenderResultListAction(
                    [
                        ExtensionResultItem(
                            icon="images/custom.png",
                            name=f"{short_url}",
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                        ExtensionResultItem(
                            icon="images/stats.png",
                            name=stats_page,
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                        ExtensionResultItem(
                            icon="images/copy.png",
                            name="Both link and stats page",
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(
                                f"Your Link: {short_url} Statistics page: {stats_page}",
                            ),
                        ),
                    ]
                )
            elif custom:
                return RenderResultListAction(
                    [
                        ExtensionResultItem(
                            icon="images/custom.png",
                            name=f"{short_url}",
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                    ]
                )
            elif stats:
                return RenderResultListAction(
                    [
                        ExtensionResultItem(
                            icon="images/link.png",
                            name=f'{short_url}',
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                        ExtensionResultItem(
                            icon="images/stats.png",
                            name=stats_page,
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                        ExtensionResultItem(
                            icon="images/copy.png",
                            name="Both link and stats page",
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(
                                f"Your Link: {short_url} Statistics page: {stats_page}",
                            ),
                        ),
                    ]
                )
            else:
                return RenderResultListAction(
                    [
                        ExtensionResultItem(
                            icon="images/link.png",
                            name=f"{short_url}",
                            description="Copy to clipboard",
                            on_enter=CopyToClipboardAction(short_url),
                        ),
                    ]
                )
        else:
            errorcode = response_data["errorcode"]
            errormessage = response_data["errormessage"]
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/warning.png",
                        name=f"Error: {self.errors.get(errorcode, 'Unknown Error')}",
                        description=errormessage,
                        on_enter=HideWindowAction(),
                    ),
                ]
            )

    def shortn(self, url, custom_url=None, log_stat=False):
        """
        Shortens the provided URL using the is.gd API.
        :param url: The URL to shorten.
        :param custom_url: An optional custom alias for the shortened URL.
        :param log_stat: Whether to enable statistics tracking for the shortened URL.
        :return: A dictionary containing the response data from the API.
        """
        # Build data to send to the API
        data = {"format": "json", "url": url, "logstats": 1 if log_stat else 0}
        if custom_url:
            data["shorturl"] = custom_url

        # Make the request to the is.gd API
        response = requests.get(f"{shortener_url}/create.php", params=data)
        response_data = response.json()
        return response_data


if __name__ == "__main__":
    # Entry point of the extension
    ShortnExtension().run()

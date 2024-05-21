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

# create an instance of logger at a module level
logger = logging.getLogger(__name__)

# is.gd api 
shortener_url = "https://is.gd"


class ShortnExtension(Extension):
    def __init__(self):
        super(ShortnExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    errors = {
        1: "Bad Request",
        2: "Not Acceptable",
        3: "Bad Gateway",
        4: "Service Unavailable",
    }

    def on_event(self, event, extension):
        query = event.get_argument() or ""

        if not query:
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="No URL provided!",
                        description="eg. google.com | google.com stats | google.com custmurl stats  ",
                        on_enter=HideWindowAction(),
                    )
                ]
            )

        query_parts = query.split()
        url = None
        custom = None
        stats = False

        # Extract the URL
        if re.match(r"\w+://", query_parts[0]):
            url = query_parts[0]
        else:
            url = "http://" + query_parts[0]

        # Extract the custom URL and the stats
        if len(query_parts) > 1:
            if query_parts[1] == "stats":
                stats = True
            else:
                custom = query_parts[1]

        if len(query_parts) > 2 and query_parts[2] == "stats":
            stats = True

        # Build the request URL
        response_data = self.shortn(url, custom, stats)

        if "shorturl" in response_data:
            # success
            short_url = response_data["shorturl"]

            stats_page = f"{shortener_url}/stats.php?url={str(response_data['shorturl'])[str(response_data['shorturl']).rindex('/') + 1:]}"
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
                            name=f"Both link and stats page",
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
                            name=f"Both link and stats page",
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

    # Shorten the URL
    def shortn(self, url, custom_url=None, log_stat=False):
        # Build data to post
        data = {"format": "json", "url": url, "logstats": 1 if log_stat else 0}
        if custom_url:
            data["shorturl"] = custom_url

        # Make the request
        response = requests.get(f"{shortener_url}/create.php", params=data)
        response_data = response.json()
        return response_data


if __name__ == "__main__":
    ShortnExtension().run()

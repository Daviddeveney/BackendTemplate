ython SDK
All the features and utilities for fast Python development with Browserbase.
If you are working with Python, the official browserbase package is the easiest way to connect and act upon headless browsers running on Browserbase.

​
Installation


pip install browserbase
​
Basic usage

Here is an example using the Browserbase Python SDK to create and connect to a session using Playwright:


from playwright.sync_api import Playwright, sync_playwright
from browserbase import Browserbase

bb = Browserbase(api_key=BROWSERBASE_API_KEY)


def run(playwright: Playwright) -> None:
    # Create a session on Browserbase
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)

    # Connect to the remote session
    chromium = playwright.chromium
    browser = chromium.connect_over_cdp(session.connect_url)
    context = browser.contexts[0]
    page = context.pages[0]

    try:
        # Execute Playwright actions on the remote browser tab
        page.goto("https://news.ycombinator.com/")
        page_title = page.title()
        assert (
        page_title == "Hacker News"
        ), f"Page title is not 'Hacker News', it is '{page_title}'"
        page.screenshot(path="screenshot.png")
    finally:
        page.close()
        browser.close()

    print(f"Done! View replay at https://browserbase.com/sessions/{session.id}")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)


Features
Sessions
Each browser run is a Session, controlled through our APIs.
​
Overview

In web automation, a browser session in web automation represents a single browser instance, from connection to termination: closure, timeout, or disconnection, running in isolated environments to ensure resource exclusivity, thereby maintaining stability and performance.

These sessions are highly configurable through APIs, allowing for adjustments to settings such as running in a selected geographic region or specifying a keep alive session.

Sessions also support on-the-fly file downloads and can be easily started with automation frameworks like Playwright, Puppeteer, or Selenium, or pre-configured using a Session API, offering flexibility and control for developers.

​
Browser configuration

Sessions run on fast instances with isolated resources (storage, network, memory, and vCPUs).

The viewport, user agents, and header configuration are handled by the fingerprint mechanism.

Downloads are enabled and stored by default, accessible via the API.

​
Sessions

​
Starting a Session

A Session is either created implicitly upon connection (via connectOverCDP() or puppeteer.connect()), or via the Sessions API.

Once created, connect to a Session through a Driver (Playwright, Puppeteer, or Selenium) or via the Session Inspector.

Node.js
Python

Playwright

Selenium

import os

import requests
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.remote_connection import RemoteConnection

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]


def create_session() -> str:
    """
    Create a Browserbase session - a single browser instance.

    :returns: The new session's ID.
    """
    sessions_url = "https://api.browserbase.com/v1/sessions"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    # Include your project ID in the JSON payload
    json = {"projectId": PROJECT_ID}

    response = requests.post(sessions_url, json=json, headers=headers)

    # Raise an exception if there wasn't a good response from the endpoint
    response.raise_for_status()
    return response.json()["id"]


class BrowserbaseConnection(RemoteConnection):
    """
    Manage a single session with Browserbase.
    """

    _session_id: str

    def __init__(self, *args, **kwargs):
        self._session_id = create_session()
        super().__init__(*args, **kwargs)

    def get_remote_connection_headers(self, parsed_url, keep_alive=False):
        headers = super().get_remote_connection_headers(parsed_url, keep_alive)

        # Update headers to include the Browserbase required information
        headers["x-bb-api-key"] = API_KEY
        headers["session-id"] = self._session_id

        return headers


def run(driver: WebDriver):
    # Instruct the browser to go to the SF MOMA page
    driver.get("https://www.sfmoma.org")

    # Print out a bit of info about the page it landed on
    print(f"{driver.current_url=} | {driver.title=}")

    ...


# Use the custom class to create and connect to a new browser session
connection = BrowserbaseConnection("http://connect.browserbase.com/webdriver")
driver = webdriver.Remote(connection, options=webdriver.ChromeOptions())

# Print a bit of info about the browser we've connected to
print(
    "Connected to Browserbase",
    f"{driver.name} version {driver.caps['browserVersion']}",
)

try:
    # Perform our browser commands
    run(driver)

finally:
    # Make sure to quit the driver so your session is ended!
    driver.quit()

You must connect to a Session within the timeout supplied during creation or the default timeout of your project.
​
Asynchronous Sessions

You can also create and manage Sessions asynchronously. This is useful if you want to run your automation in an asynchronous environment, such as an asyncio event loop.

Session Timeout

Sessions time out when running for longer than the timeout configured in your Project’s Settings:


The following code samples require the Browserbase SDK.
To keep sessions alive upon disconnections, provide the keepAlive param when creating a new Session and stop the session manually:

Node.js
Python

import os
from browserbase import Browserbase

# Initialize the SDK

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

bb = Browserbase(BROWSERBASE_API_KEY)

// Create a session with `keepAlive` set to `true`

session = bb.sessions.create(keep_alive=True, project_id=BROWSERBASE_PROJECT_ID)

// Terminate the session

bb.sessions.update(session.id, status="REQUEST_RELEASE", project_id=BROWSERBASE_PROJECT_ID)

For more information on using keep alive sessions, please refer to our Long Running Sessions guide.

We recommend that you release your keep alive sessions manually when no longer needed. They will time out eventually, but you may be charged for the unneeded browser minutes used.
​
Inspecting a Session

You can inspect a completed Session using the Session API or the Session Inspector:

Action	Session Inspector	Sessions API
Access logs	✅	Sessions API logs endpoint
Access ChromeDevTools data (ex: network, DOM events)	✅	Sessions API logs endpoint
Access recording	✅	Sessions API recording endpoint
Retrieve downloaded files	❌	Sessions API downloads endpoint
Session Live View	❌	Sessions API Live URLs endpoint
Access memory and CPUs usage	✅	❌
​
Session Concurrency and Rate Limiting

The number of concurrent browsers you can run depends on your plan:

Plan	Free	Hobby	Startup	Scale
Concurrent Browsers	1	3	50	100+
Your concurrency means two things:

You can have at most that many sessions running at the same time

You can make at most that many requests to POST /v1/sessions in a minute

When reaching the session concurrency limit of your plan, any subsequent request to create a new session will return an HTTP 429 Too Many Requests error. That means the request was effectively dropped. To check the status of your rate limit, you can look at the headers of the response:

x-ratelimit-limit - How many requests you can make.

x-ratelimit-remaining - How many requests remain in the time window.

x-ratelimit-reset - How many seconds must pass before the rate limit resets.

retry-after - If the max has been reached, this is the number of seconds you must wait before you can make another request. This is documented here.


HTTP/1.1 429 Too Many Requests
Content-Type: application/json
x-ratelimit-limit: 3
x-ratelimit-remaining: 0
x-ratelimit-reset: 45
retry-after: 45
To avoid rate limits, you can either by run fewer concurrent sessions or close sessions explicitly as opposed to letting them time out.

For example, if you have a Hobby plan with a limit of 3 concurrent sessions, you can create up to 3 sessions in a 60 second window. If you try to create a 4th session within that window, it will be rate limited and return an HTTP 429 error.

If you need more concurrency, you can upgrade to a plan that allows for a higher limit. For example, the Hobby plan allows for 3 concurrent browsers while the Startup plan increases the limit to 50. The Scale plan is customizable to the amount of concurrency that you require. If you are interested in upgrading you plan, please reach out to: support@browserbase.com

​
User Metadata

Our List Sessions endpoint supports filtering sessions by status. This is helpful but not highly configurable. User metadata allows you to attach arbitrary JSON data to sessions, which then gives you additional flexibility when querying sessions.

​
Attaching User Metadata to a Session

User metadata is attached to a session when hitting our Create Session endpoint. This metadata can be any JSON-serializable object.

This metadata is attached to the stored session object and can be queried against using the List Sessions endpoint.

Below is an example for attaching an order status to a created session. This will attach the object {"order": {"status": "shipped"}} to the created session.


curl --request POST \
  --url "https://api.browserbase.com/v1/sessions" \
  --header 'Content-Type: application/json' \
  --header 'X-BB-API-Key: <api-key>' \
  --data '{"projectId": "<project-id>", "userMetadata": {"order": {"status": "shipped"}}}'
The size of the stored JSON object is limited to 512 characters. We measure this by converting your object into a JSON string (think JSON.stringify) and measuring the length of the resulting string.
​
Querying Sessions by User Metadata

Querying using user metadata is done via the q query parameter on the List Sessions endpoint.

Let’s use the example object {"order": {"status": "shipped"}} from the previous section. To query for all sessions with an order of status "shipped", you can use the following query:


user_metadata['order']['status']:'shipped'
This query contains the following components:

user_metadata is known as the “base” of the query. Currently we only support the user_metadata base, although we’re working to support more querying bases in the future. Stay tuned!

['order']['path'] is known as the “path” of the query. The path is used to drill into nested fields in the stored metadata object. In this case, we’re looking for an object with keys in the shape { "order": { "status" }}.

'shipped' is known as the “value” of the query. This is separated from the base and the path of the query with a : character. The “value” field of the query is used to check strict equality of the value specified by the “path” of the query. In our case, we’re looking for an object with the exact shape { "order": { "status": "shipped" }}.

Note that we need to URL encode the query string to ensure that it’s properly parsed by the API.

%5B is the URL encoded version of [

%5D is the URL encoded version of ]

%3A is the URL encoded version of :

In JavaScript, you can use encodeURIComponent("user_metadata['order']['status']:'shipped'") to encode the query string.
Below is an example of how to use this query.\


curl --request GET \
  --url "https://api.browserbase.com/v1/sessions?q=user_metadata%5B'order'%5D%5B'status'%5D%3A'shipped'" \
  --header 'X-BB-API-Key: <api-key>'
This will return a list of all sessions with attached metadata in the form {"order": {"status": "shipped"}}. If the query doesn’t match any sessions, the API will respond with an empty list [].

Currently we only support querying by fields (no arrays) and checking value equality of string (no numbers or booleans). A quick workaround for this is to convert numbers and booleans into strings and query normally. Stay tuned!
Was this page helpful?

Yes

selenium Example:
from typing import Dict

from selenium import webdriver
from selenium.webdriver.remote.remote_connection import RemoteConnection

from examples import BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, bb


class BrowserbaseConnection(RemoteConnection):
    """
    Manage a single session with Browserbase.
    """

    session_id: str

    def __init__(self, session_id: str, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)  # type: ignore
        self.session_id = session_id

    def get_remote_connection_headers(  # type: ignore
        self, parsed_url: str, keep_alive: bool = False
    ) -> Dict[str, str]:
        headers = super().get_remote_connection_headers(parsed_url, keep_alive)  # type: ignore

        # Update headers to include the Browserbase required information
        headers["x-bb-api-key"] = BROWSERBASE_API_KEY
        headers["session-id"] = self.session_id

        return headers  # type: ignore


def run() -> None:
    # Use the custom class to create and connect to a new browser session
    session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
    connection = BrowserbaseConnection(session.id, session.selenium_remote_url)
    driver = webdriver.Remote(
        command_executor=connection,
        options=webdriver.ChromeOptions(),  # type: ignore
    )

    # Print a bit of info about the browser we've connected to
    print(
        "Connected to Browserbase",
        f"{driver.name} version {driver.caps['browserVersion']}",  # type: ignore
    )

    try:
        # Perform our browser commands
        driver.get("https://www.sfmoma.org")
        print(f"At URL: {driver.current_url} | Title: {driver.title}")
        assert driver.current_url == "https://www.sfmoma.org/"
        assert driver.title == "SFMOMA"

    finally:
        # Make sure to quit the driver so your session is ended!
        driver.quit()


if __name__ == "__main__":
    run()

    Sessions:
    Create a Session
POST
/
v1
/
sessions

Try it
Authorizations
​
X-BB-API-Key
string
header
required
Your Browserbase API Key.
Body
application/json
​
projectId
string
required
The Project ID. Can be found in Settings.
​
browserSettings
object

Show child attributes
​
extensionId
string
The uploaded Extension ID. See Upload Extension.
​
keepAlive
boolean
Set to true to keep the session alive even after disconnections. This is available on the Startup plan only.
​
proxies

Proxy configuration. Can be true for default proxy, or an array of proxy configurations.
​
region
enum<string>
The region where the Session should run.
Available options: us-west-2, us-east-1, eu-central-1, ap-southeast-1 
​
timeout
integer
Duration in seconds after which the session will automatically end. Defaults to the Project's defaultTimeout.
Required range: 60 < x < 21600
​
userMetadata
object
Arbitrary user metadata to attach to the session. To learn more about user metadata, see User Metadata.

Show child attributes
Response
201 - application/json
​
connectUrl
string
required
WebSocket URL to connect to the Session.
​
createdAt
string
required
​
expiresAt
string
required
​
id
string
required
​
keepAlive
boolean
required
Indicates if the Session was created to be kept alive upon disconnections
​
projectId
string
required
The Project ID linked to the Session.
​
proxyBytes
integer
required
Bytes used via the Proxy
​
region
enum<string>
required
The region where the Session is running.
Available options: us-west-2, us-east-1, eu-central-1, ap-southeast-1 
​
seleniumRemoteUrl
string
required
HTTP URL to connect to the Session.
​
signingKey
string
required
Signing key to use when connecting to the Session via HTTP.
​
startedAt
string
required
​
status
enum<string>
required
Available options: RUNNING, ERROR, TIMED_OUT, COMPLETED 
​
updatedAt
string
required
​
avgCpuUsage
integer
CPU used by the Session
​
contextId
string
Optional. The Context linked to the Session.
​
endedAt
string
​
memoryUsage
integer
Memory used by the Session
​
userMetadata
object
Arbitrary user metadata to attach to the session. To learn more about user metadata, see User Metadata.

Hide child attributes
​
userMetadata.{key}
any



Guides
Long Running Sessions
Keep browser sessions alive for as long as you need.
By default, browser sessions end when they time out or when you disconnect, whichever comes first. By specifying custom session timeouts and by using the session keep alive feature, you can keep your session running as long as necessary to meet your app’s requirements.

Session keep alive is available on the Startup and Scale plans.
​
Why keep sessions alive?

Custom timeouts and session keep alive supports a broad spectrum of use cases. Key benefits include:

Avoid interrupting long-running tasks and workflows.
Connect, disconnect, and reconnect to the same session.
Keep working with a session without worrying about it timing out.
Reusing existing sessions is more performant than creating new ones.
Your web automation framework, such as Playwright, Puppeteer, or Selenium, is responsible for disconnecting and reconnecting to browser sessions.
​
How it works

These examples illustrate using the Sessions API or the SDK to create a basic session:

Node.js
Python

API

SDK

const options = {
  method: "POST",
  headers: {
    "X-BB-API-Key": "<your-api-key>",
    "Content-Type": "application/json",
  },
  body: '{"projectId":"<your-project-id>"}',
};

fetch("https://api.browserbase.com/v1/sessions", options)
  .then((response) => response.json())
  .then((response) => console.log(response))
  .catch((err) => console.error(err));
For these examples, make sure to set your BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID environment variables. To get your API key and project ID, refer to the Settings page in your Dashboard as described in the Start your first Session Quickstart.
This creates a browser session with the default timeout for your project. Now, let’s take a look at creating sessions with custom timeouts.

​
Session timeouts

Sessions normally end when disconnecting or by timing out, whichever comes first. There is a default timeout that you can override in two different ways:

Project-wide. Set the default session timeout for your project in the Dashboard:

Any sessions created for this project will take the specified timeout as default.

Per-session. You can specify the timeout at session create time as shown here:
​
Custom session timeout

To set a custom timeout for your session, specify the timeout option in the API request body or with the SDK.

Node.js
Python

API

SDK

# Session with a custom timeout
#
import os
from pprint import pprint

import requests

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

headers = {"x-bb-api-key": BROWSERBASE_API_KEY}
json = {
    "projectId": BROWSERBASE_PROJECT_ID,
    "timeout": 3600,
}

response = requests.post(
    "https://api.browserbase.com/v1/sessions", json=json, headers=headers
)

# Raise an exception if there wasn't a good response from the endpoint.
response.raise_for_status()

# print the response
pprint(response.json())
Here the timeout has been set to 3600 seconds (1 hour), overriding the default. That means that unless explicitly closed beforehand, the session will continue running for an hour before terminating. At disconnect, it will end.

The maximum duration of a session is 6 hours. Once a session times out, it can no longer be used.
Setting a custom timeout won’t keep the session alive after disconnecting. To allow reconnecting to a session after disconnecting, it needs to be configured for keep alive.

​
Keeping sessions alive across disconnects

Browserbase offers a keepAlive feature to keep sessions alive across disconnects, allowing you to continue using it as long as needed. Setting keepAlive to true will keep the session available for later use:

Node.js
Python

API

SDK

# Create a session with the keep-alive option enabled
#
import os
from pprint import pprint

import requests

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

headers = {"x-bb-api-key": BROWSERBASE_API_KEY}
json = {
  "projectId": BROWSERBASE_PROJECT_ID,
  "keepAlive": True,
}

response = requests.post(
  "https://api.browserbase.com/v1/sessions/",
  json=json,
  headers=headers,
)

# Raise an exception if there wasn't a good response from the endpoint.

response.raise_for_status()

# print the response

pprint(response.json())
You can reconnect to the keep alive session using the Connect API. Once reconnected, it will perform as usual.

​
Stopping a keep alive session

In order to stop the session, use the Browserbase API or the SDK as shown here:

Node.js
Python

API

SDK

# Stop a session
#
import os
from pprint import pprint

import requests

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

SESSION_ID = "<The id of the session to stop>"

headers = {"x-bb-api-key": API_KEY}
json = {
    "projectId": PROJECT_ID,
    "status": "REQUEST_RELEASE",
}

response = requests.post(
    f"https://api.browserbase.com/v1/sessions/{SESSION_ID}",
    json=json,
    headers=headers,
)

# Raise an exception if there wasn't a good response from the endpoint.
response.raise_for_status()

# print the response
pprint(response.json())
We recommend that you stop your keep alive sessions explicitly when no longer needed. They will time out eventually, but you may be charged for the unneeded browser minutes used.
Was this page helpful?

Yes

Connect API
Connect API
Connect or create a Session on-the-fly.
The Connect API is available both as:

a WebSocket endpoint: wss://connect.browserbase.com
an HTTP endpoint: http://connect.browserbase.com/webdriver
Puppeteer and Playwright connect over the WebSocket API while Selenium relies on the HTTP API.

​
Puppeteer and Playwright: Connect over WebSocket

​
Authentication

The Connect WebSocket API authentication relies on the apiKey query parameter as follows:

Node.js
Python
Playwright

import os
from playwright.sync_api import sync_playwright, Playwright

def run(playwright: Playwright):
    chromium = playwright.chromium
    browser = chromium.connect_over_cdp('wss://connect.browserbase.com?apiKey='+ os.environ["BROWSERBASE_API_KEY"])
    context = browser.contexts[0]
    page = context.pages[0]

with sync_playwright() as playwright:
    run(playwright)
​
Available query parameters

On top of the apiKey query parameter, the wss://connect.browserbase.com endpoints offers the following optional parameters:

​
sessionId
string
You can pass the ID of an already created Session.
​
enableProxy
boolean
default:
"false"
Enable proxy by passing &enableProxy=true. Learn more about Proxying.
​
Selenium: Connect over HTTP

​
Custom HTTP Agent and Authentication

Selenium Node.js and Python do not yet support connecting over a WebSocket. Instead, you’ll need a provide a custom HTTP Agent that provide the required authentication header (x-bb-api-key) to connect to the http://connect.browserbase.com/webdriver endpoint as follows:


Node.js

Python

from selenium import webdriver
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
import os

def create_session():
    url = 'https://api.browserbase.com/v1/sessions'
    headers = {'Content-Type': 'application/json', 'x-bb-api-key': os.environ["BROWSERBASE_API_KEY"]}
    response = requests.post(url, json={ "projectId": os.environ["BROWSERBASE_PROJECT_ID"] }, headers=headers)
    return response.json()['id']


class CustomRemoteConnection(RemoteConnection):
    _session_id = None

    def __init__(self, remote_server_addr: str, session_id: str):
        super().__init__(remote_server_addr)
        self._session_id = session_id

    def get_remote_connection_headers(self, parsed_url, keep_alive=False):
        headers = super().get_remote_connection_headers(parsed_url, keep_alive)
        headers.update({'x-bb-api-key': os.environ["BROWSERBASE_API_KEY"]})
        headers.update({'session-id': self._session_id})
        return headers

def run():
    session_id = create_session()
    custom_conn = CustomRemoteConnection('http://connect.browserbase.com/webdriver', session_id)
    options = webdriver.ChromeOptions()
    driver = webdriver.Remote(custom_conn, options=options)
    driver.get("https://www.browserbase.com")
    get_title = driver.title
    print(get_title)
    # Make sure to quit the driver so your session is ended!
    driver.quit()

run()
​
Available headers parameters

​
session-id
string
required
The Session ID created via the HTTP API.
​
enable-proxy
string
default:
"false"
Enable proxy by passing the enable-proxy header. Learn more about Proxying.
# SimACARS

This is a simulated ACARS network for flight simulation only.

If you are flying on a network, your API key is an encrypted string of SECRET:NETWORK:USER_ID.

Your network user ID is used to verify that the callsign you have logged on with.

Your user ID is verified using your network's OAuth2 protocol. We ONLY store your encrypted user ID and flight simulation network and no other personal data.

With SimACARS, there is no longer a need to poll the server. Subscribe to [Server-Sent Events]([https://developer.mozilla.org/en-US/docs/Web/API/EventSource). This can easily be implemented in [TypeScript](https://docs.servicestack.net/typescript-server-events-client) as well!

# Running Locally
### Dependencies
 - Python >= 3.14.4
 - Python pip >= 26.1.1
 - Git >= 2.54.0 (windows)
 - Redis >= 8.0.0
 - OpenObserve >= 0.11.0 (windows)
 - OpenTelemetry Collector >= 0.107.0

### Getting Started (Visual Studio Code)
    git clone https://github.com/SimACARS/acars-server.git

Create and activate a virtual environment

Setup OpenObserve using this guide https://openobserve.ai/blog/monitoring-fastapi-application-using-opentelemetry-and-openobserve/

    pip install -r requirements.txt
    pip install opentelemetry-distro
    opentelemetry-bootstrap -a install
    pip install opentelemetry-exporter-otlp
    fastapi dev

Browse to http://127.0.0.1:8000 for the API or http://127.0.0.1:8000/docs for OpenAPI docs

# Authentication Flows
## Users
### New User (API Key Generation)
```mermaid
graph LR
A((New User)) --> B@{ shape: lean-r, label: "/user/new/NETWORK" }
B -- NETWORK OAuth2 --> C@{ shape: tri, label: "NETWORK ID" }
D@{ shape: procs, label: "Auto Generated SALT" } --> E@{ shape: hex, label: "SALT:NETWORK:CID" }
C --> E
E -- Encrypt with master.key --> F@{ shape: procs, label: "Generated API Key" }
F --> G@{ shape: curv-trap, label: "Display API Key to User" }
F --> H@{ shape: lin-cyl, label: "Store API Key" }
```

### Existing User (Message Store on VATSIM)
```mermaid
graph LR
A((Existing User)) --> B@{ shape: sl-rect, label: "API Key set via x-key header" }
B --> C@{ shape: lean-r, label: "/msg/tx" }
C --> E
E@{ shape: bow-rect, label: "API Key Lookup" } --> D@{ shape: diamond, label: "Does API Key Exist?" }
D -- Yes --> DA@{ shape: bow-rect, label: "Callsign Lookup" }
DA --> DB@{ shape: diamond, label: "Does provided callsign match CID and Sluper?" }
DB -- Yes --> F@{ shape: datastore, label: "Store Message" }
F --> G@{ shape: dbl-circ, label: "Return 201" }
DB -- No --> DC@{ shape: dbl-circ, label: "Return 403" }
D -- No --> H@{ shape: dbl-circ, label: "Return 401" }
```

### Existing User (Message Forward on VATSIM)
```mermaid
graph LR
A((Existing User)) --> B@{ shape: sl-rect, label: "API Key set via x-key header" }
B --> C@{ shape: lean-r, label: "/msg/tx" }
C --> E
E@{ shape: bow-rect, label: "API Key Lookup" } --> D@{ shape: diamond, label: "Does API Key Exist?" }
D -- Yes --> DA@{ shape: bow-rect, label: "Callsign Lookup" }
DA --> DB@{ shape: diamond, label: "Does provided callsign match CID and Sluper?" }
DB -- Yes --> F@{ shape: datastore, label: "Forward Messages to User" }
F --> G@{ shape: dbl-circ, label: "Return 201" }
DB -- No --> DC@{ shape: dbl-circ, label: "Return 403" }
D -- No --> H@{ shape: dbl-circ, label: "Return 401" }
```

## Airlines
### New Airline
Anyone can request a temporary (24hour) airline API key. Domain verification is required for a permanent API key.
```mermaid
graph LR
A((New Airline)) --> B@{ shape: lean-r, label: "POST /airline/new" }
B -- Mandatory Fields --> C@{ shape: tri, label: "airline_name, airline_callsign, network" }
C -- Optional Fields --> BA@{ shape: tri, label: "domain" }
BA -- Domain Auth --> BB@{ shape: lean-r, label: "_acars-verification.DOMAIN IN TXT 'acars-verify-TOKEN'" }
BB -- Permanent Key --> F
C -- 24 Hour Temp Key--> F@{ shape: procs, label: "Generated API Key" }
F --> G@{ shape: curv-trap, label: "Display API Key to User" }
F --> H@{ shape: lin-cyl, label: "Store API Key" }
```
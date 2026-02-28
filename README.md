This project is to provide a prototype architecture for a MMO fishing game that can scale. Each server acts as a tile in the world and is the source of truth for that tile.
The main objective is to allow nearby players to show-up on a live map with hindering performance.

Directory:
-client: Contains a test client. To run use "python3 client.py" in client/
-server: 6 node server. To run use "docker compose up" in server/
-servermono: 1 node server implentation. To run use "docker compose up" in servermono/

fishing_test.js - provides a k6 test. 
To run:
Install k6 using "brew install k6"
Run "k6 run fishing_test.js"

#### Key performance comparison:
##### 1 node system:
EXECUTION
iteration_duration...........: avg=1.02s  min=1s       med=1s     max=1.2s     p(90)=1.08s   p(95)=1.1s  
iterations...................: 1000   96.866251/s
vus..........................: 100    min=100      max=100
vus_max......................: 100    min=100      max=100

GRPC
grpc_req_duration............: avg=13.4ms min=596.66µs med=3.61ms max=176.58ms p(90)=59.39ms p(95)=79.6ms
grpc_streams.................: 1000   96.866251/s
grpc_streams_msgs_received...: 1000   96.866251/s
grpc_streams_msgs_sent.......: 5000   484.331254/s

##### 6 node system:
EXECUTION
iteration_duration...........: avg=1.01s  min=1s       med=1.01s  max=1.05s   p(90)=1.02s   p(95)=1.03s  
iterations...................: 1000   98.283894/s
vus..........................: 100    min=100      max=100
vus_max......................: 100    min=100      max=10

GRPC
grpc_req_duration............: avg=7.73ms min=806.29µs med=6.65ms max=31.33ms p(90)=14.17ms p(95)=17.01ms
grpc_streams.................: 1000   98.283894/s
grpc_streams_msgs_received...: 1000   98.283894/s
grpc_streams_msgs_sent.......: 5000   491.419472/s

fishing.proto contains the gRPC service definitions:
ListUser - lists users
login - logs in user
updatelocation - updates user's x,y
startfishing - starts fishing server stream
currentusers - tells the current number of users and as more users oopen a updatelocation stream. sends the updated player count
Inventory - lists inventory of fish at that node
getimage - a returns that servers image(represents that tiles google map's portion)

Future plans:
Add a pocketbase node(persistance and centralization of data)
Add a proper distribution network(Given x,y gps location it should return a server address)
Create a dynamic client that can connect to multiple servers at the same time to show a large scale map

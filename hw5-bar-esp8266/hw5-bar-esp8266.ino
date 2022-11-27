#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>

char* ssid= "GoogleWifi";   // wifi name
char* pass= "1234554321";   // wifi password

#define VERSIONNUMBER 28
#define LOGGERIPINC 20
#define SWARMSIZE 5
// 30 seconds is too old - it must be dead
#define SWARMTOOOLD 30000


// Packet Types
#define LIGHT_UPDATE_PACKET 0
#define LIGHT_UPDATE_PACKET_To_SERVER 1
#define RESET_ESP 2
#define DEFINE_SERVER_LOGGER_PACKET 4

int device_ID = 1;

unsigned int localPort = 8118;

int swarmClear[3];

// master variables
int masterState = 1;   // 1 if master, 0 if not

IPAddress serverAddress = IPAddress(0, 0, 0, 0); // default no IP Address

int swarmAddresses[SWARMSIZE];  // Swarm addresses

int clearColor; // variables for light sensor

const int PACKET_SIZE = 14; // Light Update Packet
const int BUFFERSIZE = 1024;

byte packetBuffer[BUFFERSIZE]; //buffer to hold incoming and outgoing packets

String packetBuffer_array;

// A UDP instance to let us send and receive packets over UDP
WiFiUDP udp;
IPAddress local_IP;

int ledPins[] = { 16,5,4,0,3,14,12,13,15,1};
const int ledCount = 10;

void setup()
{
  Serial.begin(115200);
  pinMode(A0, INPUT);
  for (int thisLed = 0; thisLed < ledCount; thisLed++) {
    pinMode(ledPins[thisLed], OUTPUT);
  }
  pinMode(2, OUTPUT);

  Serial.println("");
  Serial.println("--------------------------");
  Serial.println("LightSwarm");
  Serial.print("Version ");
  Serial.println(VERSIONNUMBER);
  Serial.println("--------------------------");

  // We start by connecting to a WiFi network
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, pass);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");

  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Starting UDP");

  udp.begin(localPort);
  Serial.print("Local port: ");
  Serial.println(udp.localPort());

  // set SwarmID based on IP address 
  local_IP = WiFi.localIP();
}

int counter;
int send_message[8];
int receive_message[8];
String pieces[8];
int lastIndex;
int device_IP_ID[] = {0,0,0};
int tmp;
void loop()
{
    clearColor = analogRead(A0);
    Serial.print("Light level: "); 
    Serial.println(clearColor);            // print the light value in Serial Monitor
    send_message[6] = clearColor;
    send_message[7] = device_ID;
    send_message[5] = masterState;
    send_message[1] = local_IP[0];
    send_message[2] = local_IP[1];
    send_message[3] = local_IP[2];
    send_message[4] = local_IP[3];

    swarmClear[device_ID - 1] = clearColor;
    
    int ledLevel = map(clearColor, 0, 1023, 0, ledCount);
    for (int thisLed = 0; thisLed < ledCount; thisLed++) {
      if (thisLed < ledLevel) {
        digitalWrite(ledPins[thisLed], HIGH);
      }
      else {
        digitalWrite(ledPins[thisLed], LOW);
      }
    }
    
    int sendToLightSwarm = 255;
    IPAddress sendSwarmAddress(192, 168, 86, sendToLightSwarm); // my Swarm Address
    sendLightUpdatePacket(sendSwarmAddress);


    // wait to see if a reply is available
    delay(100);

     int cb = udp.parsePacket();
     if (!cb) {
        Serial.println("no packet yet.................");
     } else {
      char buf[cb];
      udp.read(buf, cb);
      String myString(buf);

      Serial.println(buf);
        
      counter = 0;
      lastIndex = 0;
      for (int i = 0; i < myString.length(); i++) {
        if (myString.substring(i, i+1) == " ") {
          pieces[counter] = myString.substring(lastIndex, i);
          lastIndex = i + 1;
          counter++;
        }
        if (i == myString.length() - 1) {
          pieces[counter] = myString.substring(lastIndex, i);
        }
      }
    
      for(int i=0; i<8; i++) {
        long x = stringToLong(pieces[i]);
        receive_message[i] = x;
      }
     
    Serial.print("Pakcet type =");
    Serial.println(receive_message[0]);

    if (receive_message[0] == RESET_ESP)
    {
      Serial.print("ESP Reset");
      serverAddress = IPAddress(0, 0, 0, 0);
    }
    
    if (receive_message[0] ==  DEFINE_SERVER_LOGGER_PACKET)
    {
      Serial.println(">>>>>>>>>DEFINE_SERVER_LOGGER_PACKET Packet Recieved");
      serverAddress = IPAddress(receive_message[1], receive_message[2], receive_message[3], receive_message[4]);
      Serial.print("Server address received: ");
      Serial.println(serverAddress);
    }
    
    device_IP_ID [0] = local_IP[3];

    if (receive_message[0] == LIGHT_UPDATE_PACKET)
    {
     
   if (receive_message[4] != device_IP_ID [0] && device_IP_ID [1] == 0)
    {
      device_IP_ID [1] = receive_message[4];
    }
    if (receive_message[4] != device_IP_ID [0] && receive_message[4] != device_IP_ID [1] && device_IP_ID [2] == 0)
    {
      device_IP_ID [2] = receive_message[4];
    }
    if (device_IP_ID [0] > device_IP_ID [1] && device_IP_ID [0] > device_IP_ID [2])
    {
      if (device_IP_ID [2] > device_IP_ID [1])
      {
        tmp = device_IP_ID [1];
        device_IP_ID [1] = device_IP_ID [2];
        device_IP_ID [2] = tmp;
      }
    }
    if (device_IP_ID [1] > device_IP_ID [0] && device_IP_ID [0] > device_IP_ID [2])
    {
      tmp = device_IP_ID [0];
      device_IP_ID [0] = device_IP_ID [1];
      if (tmp > device_IP_ID [2])
      {
        device_IP_ID [1] = tmp;
      }
      if (device_IP_ID [2] > tmp)
      {
        device_IP_ID [1] = device_IP_ID [2];
        device_IP_ID [2] = tmp;
      }
    }
    if (device_IP_ID [2] > device_IP_ID [1] && device_IP_ID [2] > device_IP_ID [0])
    {
      tmp = device_IP_ID [0];
      device_IP_ID [0] = device_IP_ID [2];
      if (tmp > device_IP_ID [1])
      {
        device_IP_ID [2] = device_IP_ID [1];
        device_IP_ID [1] = tmp;
      }
      if (device_IP_ID [2] > tmp)
      {
        device_IP_ID [1] = device_IP_ID [2];
        device_IP_ID [2] = tmp;
      }
    }
    if (local_IP[3] == device_IP_ID [0])
      device_ID = 1;
    if (local_IP[3] == device_IP_ID [1])
      device_ID = 2;
    if (local_IP[3] == device_IP_ID [2])
      device_ID = 3;
      Serial.print("LIGHT_UPDATE_PACKET received from LightSwarm #");
      Serial.println(receive_message[0]);
      Serial.print("LS Packet Recieved from #");
      Serial.print(receive_message[7]);
      int receive_deviceID = receive_message[7];
      Serial.print(" SwarmState:");
      if (receive_message[5] == 0)
        Serial.print("SLAVE");
      else
        Serial.print("MASTER");
      Serial.print(" Light value:");
      Serial.print(receive_message[6]);

      // record the incoming clear color
      swarmClear[receive_deviceID - 1] = receive_message[6];
    }
    }
    // Check to see if I am master!
    checkAndSetIfMaster();
}

long stringToLong(String s)
{
    char arr[12];
    s.toCharArray(arr, sizeof(arr));
    return atol(arr);
}

char send_string[1024];
unsigned long sendLightUpdatePacket(IPAddress & address)
{
  Serial.print("sending Light Update packet to:");
  Serial.println(address);

  // set all bytes in the buffer to 0
  memset(send_message, 0, 8);
  // Initialize values needed to form Light Packet
  send_message[0] = LIGHT_UPDATE_PACKET;
  send_message[1] = local_IP[0];
  send_message[2] = local_IP[1];
  send_message[3] = local_IP[2];
  send_message[4] = local_IP[3];
  send_message[5] = masterState; 
  send_message[6] = clearColor;
  send_message[7] = device_ID; 
      
   String s = "";
   for(int i=0; i<8; i++) {
     s = s + String(int(send_message[i])) + " ";
   }
   Serial.print("Broadcast String: ");
   s.toCharArray(send_string, 1024);
   Serial.println(send_string);

  // all Light Packet fields have been given values, now
  // you can send a packet requesting coordination
  udp.beginPacketMulticast(address, localPort, WiFi.localIP());
  udp.write(send_string);
  udp.endPacket();

  return 0;
}

void checkAndSetIfMaster()
{
    int a,b,c,highest,temp;
    a = swarmClear[0];
    b = swarmClear[1];
    c = swarmClear[2];
    highest = 0;

    if (a > b) {
      highest = a;
      if (a > c) {
        highest = a;
      } else {
        highest = c;
      }
    } else {
      highest = b;
      if (b > c) {
        highest = b;
      } else {
        highest = c;
      }
    }

    if ((device_ID == 1) & (highest == a)) {
      masterState = 1;
      digitalWrite(2,LOW);
      sendLogToServer();
    } else if ((device_ID == 2) & (highest == b)) {
      masterState = 1;
      digitalWrite(2,LOW);
      sendLogToServer();
    } else if ((device_ID == 3) & (highest == c)) {
      masterState = 1;
      digitalWrite(2,LOW);
      sendLogToServer();
    } else {
      digitalWrite(2,HIGH);
      masterState = 0;
    }
}

char reply_string[1024];
void sendLogToServer() {
    send_message[0] = LIGHT_UPDATE_PACKET_To_SERVER;
    send_message[1] = local_IP[0];
    send_message[2] = local_IP[1];
    send_message[3] = local_IP[2];
    send_message[4] = local_IP[3];
    send_message[5] = masterState;
    send_message[6] = clearColor;
    send_message[7] = device_ID;
    String s = "";
    for(int i=0; i<8; i++) {
      s = s + String(int(send_message[i])) + " ";
    }
    Serial.print("String: ");
    s.toCharArray(reply_string, 1024);
    Serial.println(reply_string);
    udp.beginPacket(serverAddress, localPort);
    udp.write(reply_string);
    udp.endPacket();
    //return 0;
}

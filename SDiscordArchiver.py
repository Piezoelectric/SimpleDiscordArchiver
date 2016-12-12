import requests
import webbrowser #opens the webpage for the user to click authorize button
import json
import time
import datetime #only used at the end, to indicate when a log was taken
import codecs
import os #used to delete the reversed log, once the complete log is generated
import glob #used to find config.txt

'''
Dec 12 2016
ADDED:
1) config.txt (force a user to get their own application/hiding my own tokens)
2) Guilds menu
3) small update to instructions (must include localhost:5000 on your application)

So now SDA can get every kind of text channel!

TODO:
1) get rid of that awful copypaste stuff, set up localhost:5000 to do it automatically
using flask or something
2) put a log in its own folder, and attachments in a subfolder, rather than
barfing them all up into the same directory
'''

#====MESSAGE WRITING FUNCTIONS====
def writeMessages(channelName, channelID, messages):
    #prettifies retrieved messages from getMessages
    filenameRev = channelName+"-"+channelID+"-reversed.txt"
    filehandleRev = codecs.open(filenameRev, 'a', 'utf-8')
    
    for msg in messages:
        t = msg['timestamp']
        timestamp = t[0:10] + " " + t[11:19]
        username = msg['author']['username'] + "#" + msg['author']['discriminator']
        messagebody = (msg['content'])

        attachmentList = msg['attachments']
        if (len(attachmentList) > 0):
            messagebody = messagebody + "\n[attached: "
            for attachment in attachmentList:
                attachID = attachment['id']
                attachName = attachment['filename']
                attachURL = attachment['url']
                messagebody = messagebody + attachID +"-"+ attachName + ", "
                
                f = open(channelName+"-"+attachID+"-"+attachName, 'wb')
                f.write(requests.get(attachURL).content)
                f.close()
                #http://stackoverflow.com/a/14962401
            messagebody = messagebody + "]"

        message = "[UTC " + timestamp + "] " + username + ": " + messagebody + "\n"
        filehandleRev.write(message)

    filehandleRev.flush() #puts all messages in memory into the file
    #print("writeMessages() has finished.")

def fileReverse(channelName, channelID):
    #reverses a full message log
    filenameRev = channelName+"-"+channelID+"-reversed.txt"
    filehandleRev = codecs.open(filenameRev, 'r', 'utf-8')
    lines = filehandleRev.readlines()
    lines.reverse()

    filename = "MESSAGE-LOG-"+channelName+"-"+channelID+".txt"
    filehandle = codecs.open(filename, 'w', 'utf-8')
    filehandle.write("Log for channel '" + channelName + "', created at " + str(datetime.datetime.now()) + "\n")
    filehandle.write("Created in Simple Discord Archiver v07.\n\n")
    for line in lines:
        filehandle.write(line)
        filehandle.flush()

    #clean up
    filehandleRev.close()
    os.remove(filenameRev)

    print("fileReverse() has finished.")

#====CHANNEL RETRIEVAL FUNCTIONS====
def getDMChannels(localToken):
    userChannelsGET = "https://discordapp.com/api/users/@me/channels?token="+localToken+"&limit=100"
    response = requests.get(userChannelsGET)
    
    userChannels = json.loads(response.content.decode("utf-8"))
    print("Found " + str(len(userChannels)) + " DMs.")
    for i in range(len(userChannels)):
        channel = userChannels[i]
        print("["+str(i)+"]: " + channel["recipient"]["username"])

    print("Enter the number of the channel you want to archive.")
    chanNumber = int(input(">"))
    channel = userChannels[chanNumber]
    chanName = channel["recipient"]["username"]+"-DM"
    chanID = channel["id"]
    return chanID, chanName

def getUserGuild(localToken):
    userGuildsGET = "https://discordapp.com/api/users/@me/guilds"
    response = requests.get(userGuildsGET, headers=OAUTHhead)

    userGuilds = json.loads(response.content.decode('utf-8'))
    print("Found " + str(len(userGuilds)) + " servers.")
    for i in range(len(userGuilds)):
        guild = userGuilds[i]
        print("["+str(i)+"]: " + userGuilds[i]["name"])

    print("Enter the number of the server you want to access.")
    guildNumber = int(input(">"))
    guildID = userGuilds[guildNumber]["id"]
    guildName = userGuilds[guildNumber]["name"]
    return guildID, guildName

def getChannelFromGuild(localToken, guildID, guildName):
    guildGET = "https://discordapp.com/api/guilds/"+guildID+"/channels?token="+localToken
    response = requests.get(guildGET)

    guildChannels = json.loads(response.content.decode('utf-8'))
    guildTextChannels = []
    for channel in guildChannels: #filter out voice channels
        if channel["type"] == "text":
            guildTextChannels.append(channel)
            
    print("Found " + str(len(guildTextChannels)) + " text channels in this server.")
    for i in range(len(guildTextChannels)):
        channel = guildTextChannels[i]
        print("["+str(i)+"]: " + guildTextChannels[i]["name"])

    print("Enter the number of the channel you want to archive.")
    chanNumber = int(input(">"))
    channel = guildChannels[chanNumber]
    chanName = "channel-"+channel["name"]+"-in-"+guildName
    chanID = channel["id"]
    return chanID, chanName

#====MESSAGE RETRIEVAL FUNCTIONS====
def getMessages(localToken, channelID, channelName):
    counter = 0

    chanMessagesGET = "https://discordapp.com/api/channels/"+channelID+"/messages?token="+localToken
    response = requests.get(chanMessagesGET)
    messages = json.loads(response.content.decode("utf-8"))

    while len(messages) != 0:
        print("DEBUG: Retrieving messages " + str(counter+1) + " to " +str(counter+100))
        counter = counter+100
        writeMessages(channelName, channelID, messages) #prettifies and writes the "messages" JSON-object
        print("Ok, resting.")
        time.sleep(5)
        
        #get the next set of messages
        before = messages[len(messages)-1]['id']
        chanMessagesGET = "https://discordapp.com/api/channels/"+channelID+"/messages?token="+localToken+"&limit=100"+"&before="+before
        response = requests.get(chanMessagesGET)
        messages = json.loads(response.content.decode("utf-8"))

    print("Message retrieval for " + channelName + " is done.")
    fileReverse(channelName, channelID)
    print("getMessages() has finished.")

#====MAIN====
print("Thank you for using Simple Discord Archiver.\n")

#FIND CONFIG.TXT + Load clientID, clientSecret, localToken
cfg = glob.glob('./config.txt')
if len(cfg) == 0:
    print("\nconfig.txt not found. Initializing first-time setup.")
    configHandle = open("config.txt", 'w')
    print('''
Please log onto the Discord website, and go to
https://discordapp.com/developers/applications/me
and register a new application.

In the Redirect URI(s) field, you must add https://localhost:5000.

The application should have a ClientID and a Client Secret.
Enter these into Simple Discord Archiver, but do not share them
anywhere else. 

Press ENTER to continue.
    ''')
    input("")
    clientID = input("Please enter the ClientID.\n>")
    configHandle.write(clientID+"\n")
    clientSecret = input("Please enter the Client Secret.\n>")
    configHandle.write(clientSecret+"\n")
    print('''
To export private DMs, this program also needs your local storage token.
Please follow these instructions to access your local token:
1) Open Discord.
2) Press CTRL-SHIFT-I. This will bring up the console.
3) Type "localStorage.token" into the console and press ENTER. (This is caps sensitive.)
This will bring up a string of characters. 
    ''')
    localToken = input("Enter your local token below, without any quotes:\n>")
    configHandle.write(localToken+"\n")
    configHandle.close()
    print("\nFirst-time setup complete. Press ENTER to continue.")
    input("")
else:
    print("Loading config.txt.")
    configHandle = open("config.txt", 'r')
    clientID = (configHandle.readline()).rstrip()
    clientSecret = (configHandle.readline()).rstrip()
    localToken = (configHandle.readline()).rstrip()
    configHandle.close()
    print("Config.txt loaded. Press ENTER to continue.")
    input("")

#GETS OAUTH CODE to swap for token, etc
print('''When you press ENTER, a web browser window should appear, asking you for 
account authorization. Please click the authorize button; the program needs
to access your account in order to access your messages.

After clicking authorize, the webpage will attempt to load a URL,
which will look like this:

http://localhost:5000/#code=<CODE>

The webpage will never load because I still need to work on that.
For the time being, please copypaste the <CODE> into the command line.

Press ENTER to continue.''')
input("")
authURL = "https://discordapp.com/oauth2/authorize?client_id="+clientID+"&scope=guilds+identify&uri=https://localhost:5000&response_type=code"
webbrowser.open(authURL)

print("Please enter the code:")
code = input(">")

authRequestURL = "https://discordapp.com/api/oauth2/token?client_id="+clientID+"&client_secret="+clientSecret+"&"
authRequestURL = authRequestURL + "grant_type=authorization_code&code=" + code + "&redirect_uri=https://localhost:5000"
response = requests.post(authRequestURL)
auth = json.loads(response.content.decode("utf-8"))
OAUTHtoken = auth["access_token"]
OAUTHhead = {"Authorization": "Bearer " + OAUTHtoken}
print("\nOAUTH2 Token obtained. Program is ready to begin retrieving messages.\n")

#MAIN
channelType = ""
print("Archive private DMs or server messages? 1 for DMs, 2 for server messages")
while channelType != "1" and channelType != "2":
    channelType = input(">")
    
    if channelType == "1":
        channelID, channelName = getDMChannels(localToken)
        getMessages(localToken, channelID, channelName)
    
    elif channelType == "2":
        guildID, guildName = getUserGuild(localToken)
        channelID, channelName = getChannelFromGuild(localToken, guildID, guildName)
        getMessages(localToken, channelID, channelName)

    else:
        print("Your input was not recognized. Try again.")

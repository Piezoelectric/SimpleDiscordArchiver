import requests
import webbrowser #opens the webpage for the user to click authorize button
import json
import time
import datetime #only used at the end, to indicate when a log was taken
import codecs
import os #used to delete the reversed log, once the complete log is generated

'''
Dec 3 2016
Release for Global Hack Day
NOTE: The "Client ID" and "Client Secret" parameters have been stripped
from this file. To run this, get your own Client ID and Client Secret from
here:
https://discordapp.com/developers/applications/me
and click "New Application"


This code will NOT FUNCTION without Client ID and Client Secret
'''

#MESSAGE WRITING FUNCTIONS
def writeMessages(channelName, channelID, messages):
    #prettifies retrieved messages
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

def fileReverse(channelName, channelID):
    #reverses a full message log
    filenameRev = channelName+"-"+channelID+"-reversed.txt"
    filehandleRev = codecs.open(filenameRev, 'r', 'utf-8')
    lines = filehandleRev.readlines()
    lines.reverse()

    filename = channelName+"-"+channelID+"-LOG.txt"
    filehandle = codecs.open(filename, 'w', 'utf-8')
    filehandle.write("Log for channel '" + channelName + "', created at " + str(datetime.datetime.now()) + "\n")
    filehandle.write("Created in Simple Discord Archiver v07.\n\n")
    for line in lines:
        filehandle.write(line)
        filehandle.flush()

    #clean up
    filehandleRev.close()
    os.remove(filenameRev)

#MESSAGE RETRIEVAL FUNCTIONS
def getDMs(localToken):
    counter = 0
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

    chanMessagesGET = "https://discordapp.com/api/channels/"+chanID+"/messages?token="+localToken
    response = requests.get(chanMessagesGET)
    messages = json.loads(response.content.decode("utf-8"))

    while len(messages) != 0:
        print("DEBUG: Now on iteration " + str(counter))
        counter = counter+1
        writeMessages(chanName, chanID, messages)
        print("Ok, resting.")
        time.sleep(5)
        
        #get the next set of messages
        before = messages[len(messages)-1]['id']
        chanMessagesGET = "https://discordapp.com/api/channels/"+chanID+"/messages?token="+localToken+"&limit=100"+"&before="+before
        response = requests.get(chanMessagesGET)
        messages = json.loads(response.content.decode("utf-8"))

    print("Message retrieval for " + chanName + " is done.")
    fileReverse(chanName, chanID)
    print("Simple Discord Archiver has finished.")

'''
==========MAIN===========
'''

#GETS OAUTH TOKEN
print('''Thank you for using Simple Discord Archiver.

When you press ENTER, a web browser window should appear, asking you for 
account authorization. Please click the authorize button; the program needs
to access your account in order to access your messages.

After clicking authorize, the webpage will attempt to load a URL,
which will look like this:

http://localhost:5000/#code=<CODE>

The webpage will never load because I still need to work on that shit.
For the time being, please copypaste the <CODE> into the command line.

Press ENTER to continue.''')
input("")
authURL = "https://discordapp.com/oauth2/authorize?client_id=<ID>&scope=guilds+identify&uri=https://localhost:5000&response_type=code"
webbrowser.open(authURL)

print("Please enter the code:")
code = input(">")

authRequestURL = "https://discordapp.com/api/oauth2/token?client_id=<ID>&client_secret=<SECRET>&"
authRequestURL = authRequestURL + "grant_type=authorization_code&code=" + code + "&redirect_uri=https://localhost:5000"
response = requests.post(authRequestURL)
auth = json.loads(response.content.decode("utf-8"))
OAUTHtoken = auth["access_token"]
OAUTHhead = {"Authorization": "Bearer " + OAUTHtoken}
print("OAUTH2 Token obtained.\n")


#GET LOCAL TOKEN
print('''To export private DMs, this program needs your local storage token.
Please follow these instructions to access your local token:
1) Open Discord.
2) Press CTRL-SHIFT-I. This will bring up the console.
3) Type "localStorage.token" into the console.
This will bring up a long string of characters. 
''')
print("Enter your local token below, without any quotes:")
localToken = input(">")
print("Local token obtained.\n")

#MAIN
print("============Setup complete.============")
channelType = ""
print("Archive DMs or a guild? 1 for DMs, 2 for guilds (NOT YET IMPLEMENTED)")
while channelType != "1" and channelType != "2":
    channelType = input(">")
    
    if channelType == "1":
        getDMs(localToken)
    
    elif channelType == "2":
        userGuildsGET = "https://discordapp.com/api/users/@me/guilds"
        response = requests.get(userGuildsGET, headers=OAUTHhead)
        print(response)

    else:
        print ("Your input was not recognized. Try again.")

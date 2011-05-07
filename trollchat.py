import xchat, urllib, os, random, time

__module_name__        = "trollchat"
__module_version__     = "0.1"
__module_description__ = "extreme trolling"

troll_master = None
peons = []
trolls = []

# our current troll!
hook = None
hsay = []

def parse_trolls():
    global trolls
       
    f = open(__file__.replace('trollchat.py', 'trolls.txt'))
    
    trolls = []
    buffer = []
    
    for line in f:
        line = line.strip()
        
        if line == '':
            trolls.append(buffer)
            buffer = []
        else:
            buffer.append(line)
    
    if len(buffer) > 0:
        trolls.append(buffer)

def get_page(user, cmd = None):
    url = 'http://troll.nitrated.net/?user=' + urllib.quote_plus(user)
    
    if cmd is not None:
        url += '&cmd=' + urllib.quote_plus(cmd)
        
    wp = urllib.urlopen(url)
    r = wp.read()
    wp.close()
    
    return r

def update_troll_master():
    global troll_master

    context = xchat.find_context(channel='#newvce')
    user    = xchat.get_info('nick')
    
    # xchat bugz :D
    context.get_info('channel')
    
    # user list
    context_users = map(lambda x: x.nick, context.get_list('users'))
        
    # have we even set a troll master?
    if troll_master is None:
        troll_master = get_page(user)
        
    if troll_master not in context_users:
        troll_master = get_page(user, 'stale')

    # confirm with the troll master
    if troll_master != xchat.get_info('nick'):
        xchat.command("CTCP {0} TROLLCHAT master".format(troll_master))
    
def update_peons():
    global troll_master, peons
    
    context = xchat.find_context(channel='#newvce')
    
    # xchat bugz
    context.get_info('channel')
    
    # user list
    user_list = map(lambda x: x.nick, context.get_list('users'))

    # remove any bad ones
    peons = filter(lambda x: x in user_list, peons)

def peon_say(say):
    xchat.command("MSG #newvce {0}".format(say))

def on_user_join(word, word_eol, userdata):
    global troll_master
    user, channel, host = word
    
    # are we joining #newvce?
    if channel == '#newvce':
        update_troll_master()
    
    return None

def on_join(word, word_eol, userdata):
    global troll_master, peons, trolls, hook, hsay
    
    user, channel, host = word
    
    if channel != '#newvce':
        return None

    # temporary
    if troll_master is None:
        update_troll_master()
    
    if troll_master != xchat.get_info('nick'):
        return None

    update_peons()
    
    # is our joining user a peon?
    if user in peons or hook != None:
        return None
        
    # troll the shit out of them
    # how many trolls do we have?
    gtrolls = filter(lambda x: len(x) <= len(peons) + 1, trolls)
    
    if len(gtrolls) == 0:
        return None
        
    # troll them
    troll = random.choice(gtrolls)
    
    # now make the troll 'good'
    troll = map(lambda x: x.replace('{$USER}', user), troll)
    
    # our trollers
    trollers = [troll_master] + peons[:]
    
    random.shuffle(trollers)

    hsay = []
    
    i = 0
    for line in troll:
        hsay.append([trollers[i],line])
        i += 1
    
    # hook dat shit    
    xchat.hook_timer(100, say_next_line)

    return None

def say_next_line(ud):
    global hsay
    
    if len(hsay) > 0:
        xchat.command("CTCP {0} TROLLCHAT say {1}".format(hsay[0][0],hsay[0][1]))
        
        # did we send this to ourself?
        if hsay[0][0] == xchat.get_info('nick'):
            del hsay[0]
            xchat.hook_timer(100, say_next_line)

    return False

def on_chan_msg(word, word_eol, userdata):
    global hsay
    
    if xchat.get_info('nick') != troll_master:
        return None
    
    if xchat.get_context().get_info('channel') != '#newvce':
        return None
       
    user, text = word

    # have we seen the first line?
    if len(hsay) > 0 and text == hsay[0][1]:
        del hsay[0]
        
        if len(hsay) > 0:
            xchat.hook_timer(100, say_next_line)
            
    return None
    
def on_ctcp(word, word_eol, userdata):
    global troll_master, peons
    
    text, user = word
    
    # only intercept trollchat messages
    if 'TROLLCHAT' not in text:
        return None
    
    text = text[10:]
    
    if text == 'master':
        # are we actually the master?
        if troll_master != xchat.get_info('nick'):
            xchat.command("CTCP {0} TROLLCHAT update".format(user))
        else:
            # add this user to our peons list
            if user not in peons and user != troll_master:
                peons.append(user)

    if text == 'update':
        update_troll_master()

    if text[0:3] == 'say':
        # maybe something bad happened
        if troll_master != user:
            update_troll_master()
        if troll_master == user:
            peon_say(text[4:])
    
    # eat this mofo
    return xchat.EAT_ALL
    
def on_ctcp_send(word, word_eol, userdata):
    if 'TROLLCHAT' in word[1]:
        return xchat.EAT_ALL
    return None
        
def confirm_master(ud):
    global troll_master
    
    if troll_master != xchat.get_info('nick'):
        xchat.command("CTCP {0} TROLLCHAT master".format(troll_master))

    # keep doing this forever
    return 1
    
xchat.hook_print('You Join', on_user_join)
xchat.hook_print('Join', on_join)
xchat.hook_print('CTCP Generic', on_ctcp)
xchat.hook_print('CTCP Send', on_ctcp_send)
xchat.hook_print('Channel Message', on_chan_msg)
xchat.hook_timer(15000, confirm_master)
parse_trolls()
update_troll_master()

from utils import sqldatabase
import main


database = main.database


def make_activity():
    index = database.get_attr("index", ".")
    for guildid in index:
        for userid in index[guildid]:
            xp = index[guildid][userid]['xp']
            messages = index[guildid][userid]['messages']
            activity = index[guildid][userid]['activity']
            print(xp, sum(activity))
            values = [int(guildid), int(userid), messages] + activity
            print(values)
            sqldatabase.execute("REPLACE INTO activity VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                tuple(values))


def make_badges():
    for user in database.get_attr("users", ".", []):
        badges = database.get_attr("users", f"{user}.badges")
        if badges is None:
            continue
        sqldatabase.execute("""REPLACE INTO badges VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (int(user),
                             (1 if "developer" in badges else 0),
                             (1 if "patron" in badges else 0),
                             (1 if "super_hugger" in badges else 0),
                             (1 if "best_friend" in badges else 0),
                             (1 if "master_fisher" in badges else 0),
                             (1 if "lucky_fisher" in badges else 0),
                             (1 if "generous_fisher" in badges else 0),
                             ))


def make_customcommands():
    for guild in database.get_attr("guilds", "."):
        for command in database.get_attr("guilds", f"{guild}.custom_commands", []):
            sqldatabase.execute("""REPLACE INTO customcommands VALUES (?, ?, ?)""",
                                (int(guild), command,
                                 database.get_attr("guilds", f"{guild}.custom_commands.{command}")))


def make_fishy():
    usersdb = database.get_attr("users", ".")
    for userid in usersdb:
        sqldatabase.execute("""REPLACE INTO fishy VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (int(userid),
                             usersdb[userid].get("fishy_timestamp"),
                             usersdb[userid].get("fishy"),
                             usersdb[userid].get("fishy_gifted"),
                             usersdb[userid].get("fish_trash"),
                             usersdb[userid].get("fish_common"),
                             usersdb[userid].get("fish_uncommon"),
                             usersdb[userid].get("fish_rare"),
                             usersdb[userid].get("fish_legendary")
                             ))


def make_guilds_roles_votechannels():
    guilds = database.get_attr("guilds", ".")
    for guild_id in guilds:
        muterole = guilds[guild_id].get('muterole')
        autorole = guilds[guild_id].get('autorole')
        levelup_toggle = guilds[guild_id].get('levelup_messages', True)
        levelup_toggle = 1 if levelup_toggle else 0

        welcome_toggle = guilds[guild_id].get('welcome', True)
        welcome_toggle = 1 if welcome_toggle else 0
        welcome_channel = guilds[guild_id].get('welcome_channel')
        welcome_message = guilds[guild_id].get('welcome_message')

        starboard_toggle = guilds[guild_id].get('starboard', False)
        starboard_toggle = 1 if starboard_toggle else 0
        starboard_channel = guilds[guild_id].get('starboard_channel')
        starboard_amount = guilds[guild_id].get('starboard_amount', 3)

        rolepicker_channel = None

        sqldatabase.execute("REPLACE INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (guild_id, muterole, autorole, levelup_toggle, welcome_toggle, welcome_channel,
                             welcome_message,
                             starboard_toggle, starboard_channel, starboard_amount, rolepicker_channel))

        for role in guilds[guild_id].get('roles', []):
            role_id = guilds[guild_id]['roles'][role]
            sqldatabase.execute("REPLACE INTO roles VALUES (?, ?, ?)", (guild_id, role, role_id))

        for channel_id in guilds[guild_id].get('vote_channels', []):
            sqldatabase.execute("REPLACE INTO votechannels VALUES (?, ?)", (guild_id, channel_id))


def make_notifications():
    notifs = database.get_attr("notifications", ".")
    for guildid in notifs:
        for keyword in notifs[guildid]:
            for userid in notifs[guildid][keyword]:
                print(guildid, userid, keyword)
                sqldatabase.execute("REPLACE INTO notifications VALUES (?, ?, ?)",
                                    (int(guildid), int(userid), keyword))


def make_users():
    usersdb = database.get_attr("users", ".")
    for userid in usersdb:
        sqldatabase.execute("""REPLACE INTO users VALUES (?, ?, ?, ?);""",
                            (int(userid),
                             usersdb[userid].get("lastfm_username"),
                             usersdb[userid].get("sunsign"),
                             None))


def full_package():
    print("starting full database move...")
    make_activity()
    make_badges()
    make_customcommands()
    make_fishy()
    make_guilds_roles_votechannels()
    make_notifications()
    make_users()
    print("Database moved succesfully")

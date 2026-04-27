import discord

class State:
    events = {}
    players = {}

    @classmethod
    def get_eventView(cls, channel_id):
        return State.events.get(channel_id)

    @classmethod
    def set_eventView(cls, channel_id, event_view):
        State.events[channel_id] = event_view  

    @classmethod
    def clear_events(cls):
        State.events.clear()

    @classmethod
    def remove_event(cls, channel_id):
        State.events.pop(channel_id, None)

    @classmethod
    def is_event_running(cls, channel_id):
        return channel_id in State.events
    
    @classmethod
    def get_player_name(cls, player_mention):
        return cls.players.get(player_mention) or player_mention
    
    @classmethod
    def set_player_name_by_guild(cls, guild, player):
        if cls.players.get(player.get_mention()) is None:
            member: discord.Member = guild.get_member(player.get_id())
            if member:
                cls.players[player.get_mention()] = member.display_name
    
    @classmethod
    def set_player_name(cls, player_mention, name):
        cls.players[player_mention] = name
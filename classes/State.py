class State:
    events = {}

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
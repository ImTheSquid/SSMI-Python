import requests


# Pass URL as ip+port with "/" as final character
def bind_event(url, game, event, min_value, max_value, icon):
    json_dict = {
        "game": game,
        "event": event,
        "min_value": min_value,
        "max_value": max_value,
        "value-optional": False,
        "handlers": [{
            # Only handle Apex keyboards
            "device-type": "screened-128x40",
            "zone": "one",
            "mode": "screen",
            "datas": [{
                "icon-id": icon,
                "lines": [
                    {
                        "has-text": True,
                        "context-frame-key": "first-line"
                    },
                    {
                        "has-text": True,
                        "context-frame-key": "second-line"
                    },
                    {
                        "has-progress-bar": True
                    }
                ],

            }]
        }]
    }
    return requests.post(url + "bind_game_event", json=json_dict)


# Call this function BEFORE binding the event if a custom title/dev name is needed
def game_metadata(url, game, friendly, author):
    json_dict = {"game": game, "game_display_name": friendly, "developer": author}
    return requests.post(url + "game_metadata", json=json_dict)


def update_event(url, game, event, line_one, line_two, progress_percent):
    json_dict = {"game": game, "event": event, "data": {"value": progress_percent, "frame": {"first-line": line_one,
                                                                                             "second-line": line_two}}}
    return requests.post(url + "game_event", json=json_dict)


def remove_game(url, game):
    json_dict = {"game": game}
    return requests.post(url + "remove_game", json=json_dict)

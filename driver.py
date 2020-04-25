from time import sleep

import ssmi


def print_stat(r):
    if r.status_code == 200:
        return "[200]"
    else:
        return "[" + str(r.status_code) + "] " + str(r.content)


# Subject to change, should be updated every time computer restarts
target = "http://127.0.0.1:49391/"
print(print_stat(ssmi.game_metadata(target, "SSMI", "SteelSeries Media Integration", "Jack Hogan")))
print(print_stat(ssmi.bind_event(target, "SSMI", "UPDATE", 0, 100, 23)))

for i in range(0, 11):
    result = ssmi.update_event(target, "SSMI", "UPDATE", "song title", "song artist", i * 10)
    print(str(i) + " " + print_stat(result))
    sleep(1)

print(print_stat(ssmi.remove_game(target, "SSMI")))

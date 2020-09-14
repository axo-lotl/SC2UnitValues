import os
import mpyq
import numpy as np
from s2protocol import versions
from game_data import GameData


def get_replay_files():
    """
    :return: a list of sc2 replay file paths
    """
    replay_files = []
    for dirpath, dirs, files in os.walk(os.path.join(os.path.curdir, "replays")):
        for file in files:
            replay_files.append(os.path.join(dirpath, file))
    return replay_files


def get_events(replay_file):
    """
    :param replay_file: path to a sc2replay file
    :return: events: a list of upgrade, unit born, and unit death events
    """
    archive = mpyq.MPQArchive(replay_file)
    header = versions.latest().decode_replay_header(archive.header['user_data_header']['content'])
    base_build = header['m_version']['m_baseBuild']
    decoder = versions.build(base_build)
    game_events_gen = decoder.decode_replay_game_events(archive.read_file('replay.game.events'))
    tracker_events_gen = decoder.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))

    relevant_tracker_event_types = ["NNet.Replay.Tracker.SUnitDiedEvent",
                                    "NNet.Replay.Tracker.SUnitBornEvent",
                                    "NNet.Replay.Tracker.SUnitTypeChangeEvent",
                                    "NNet.Replay.Tracker.SUnitInitEvent",
                                    "NNet.Replay.Tracker.SPlayerSetupEvent"]

    tracker_events = [event for event in tracker_events_gen if event['_event'] in relevant_tracker_event_types]
    game_events = [event for event in game_events_gen if event['_event'] == "NNet.Game.SGameUserLeaveEvent"]

    return tracker_events + game_events


def get_nparray(replay_file):
    events = get_events(replay_file)
    game_data = GameData()
    game_data.record_events(events)
    return game_data.convert_to_nparray()


if __name__ == '__main__':
    unit_type_names = set([])
    replay_files = get_replay_files()
    if not os.path.exists("data"):
        os.makedirs("data")
    for i in range(len(replay_files)):
        print("Processed replay #{0} of {1}: {2}".format(i + 1, len(replay_files), replay_files[i]))
        data_file_name = "data/" + "".join(c for c in replay_files[i] if c.isalnum())
        np.save(file=data_file_name, arr=get_nparray(replay_files[i]))


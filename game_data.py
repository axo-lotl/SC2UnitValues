import numpy as np


class GameData(object):

    n_state_indices = 51

    _unit_type_to_index = {
        'Drone': 0,
        'DroneBurrowed': 0,
        'Queen': 1,
        'QueenBurrowed': 1,
        'Zergling': 2,
        'ZerglingBurrowed': 2,
        'Baneling': 3,
        'BanelingBurrowed': 3,
        'Roach': 4,
        'RoachBurrowed': 4,
        'Ravager': 5,
        'RavagerBurrowed': 5,
        'Hydralisk': 6,
        'HydraliskDen': 6,
        'Mutalisk': 7,
        'LurkerMP': 8,
        'LurkerMPBurrowed': 8,
        'SwarmHostMP': 9,
        'SwarmHostMPBurrowed': 9,
        'Infestor': 10,
        'InfestorBurrowed': 10,
        'Corruptor': 11,
        'Viper': 12,
        'UltraliskBurrowed': 13,
        'BroodLord': 14,
        'Probe': 15,
        'Zealot': 16,
        'Stalker': 17,
        'Sentry': 18,
        'Adept': 19,
        'HighTemplar': 20,
        'DarkTemplar': 21,
        'Immortal': 22,
        'Colossus': 23,
        'Disruptor': 24,
        'Archon': 25,
        'Observer': 26,
        'ObserverSiegeMode': 26,
        'WarpPrism': 27,
        'WarpPrismPhasing': 27,
        'Phoenix': 28,
        'VoidRay': 29,
        'Oracle': 30,
        'Tempest': 31,
        'Carrier': 32,
        'Mothership': 33,
        'SCV': 34,
        'Marine': 35,
        'Marauder': 36,
        'Ghost': 37,
        'GhostAlternate': 37,
        'Hellion': 38,
        'HellionTank': 38,
        'SiegeTank': 39,
        'SiegeTankSieged': 39,
        'Cyclone': 40,
        'WidowMine': 41,
        'WidowMineBurrowed': 41,
        'Thor': 42,
        'ThorAP': 42,
        'VikingAssault': 43,
        'VikingFighter': 43,
        'Medivac': 44,
        'Liberator': 45,
        'LiberatorAG': 45,
        'Raven': 46,
        'Banshee': 47,
        'Battlecruiser': 48
    }

    n_unit_indices = 49
    result_index = 49
    game_loop_index = 50

    _normalization_constant = 200

    def __init__(self):
        self.normalized_states = []
        self._pid_to_unit_dicts = {1: {}, 2: {}}
        self._current_state = [0] * self.n_state_indices
        self._uid_to_pid = {}
        self._total_units = 0

    def record_events(self, events):
        """
        :param events: A list of events of the relevant types.
        """
        # Find the player setup and player leave events first.
        player_events = [e for e in events if e['_event'] == "NNet.Replay.Tracker.SPlayerSetupEvent" or
                         e['_event'] == "NNet.Game.SGameUserLeaveEvent"]

        setup_events = [e for e in player_events if e['_event'] == "NNet.Replay.Tracker.SPlayerSetupEvent"]
        for event in setup_events:
            self._uid_to_pid[event['m_userId']] = event['m_playerId']

        leave_events = [e for e in player_events if e['_event'] == "NNet.Game.SGameUserLeaveEvent"]
        leave_events.sort(key=lambda e: e['_gameloop'])

        loser_pid = None
        for event in leave_events:
            uid = event['_userid']['m_userId']
            if uid in self._uid_to_pid and loser_pid is None:
                loser_pid = self._uid_to_pid[uid]

        self._current_state[self.result_index] = 1 if loser_pid == 2 else -1

        for event in sorted(events, key=lambda e: e['_gameloop']):
            self._record_unit_event(event)

    def _append_normalized_current_state(self):
        if self._total_units <= 0:
            return
        else:
            normalized_state = self._current_state.copy()
            for i in range(self.n_unit_indices):
                normalized_state[i] *= self._normalization_constant / self._total_units
            self.normalized_states.append(normalized_state)

    def _record_unit_event(self, event):
        """
        :param event: A single event. Expected to be supplied ordereded by _gameloop.
        """
        event_type = event['_event']
        if event_type == "NNet.Replay.Tracker.SUnitBornEvent" or event_type == "NNet.Replay.Tracker.SUnitInitEvent":
            type_name = str(event['m_unitTypeName'], 'utf-8')
            if type_name not in self._unit_type_to_index:
                return
            type_index = self._unit_type_to_index[type_name]
            pid = event['m_controlPlayerId']
            if pid not in self._pid_to_unit_dicts:
                return
            tag = event['m_unitTagIndex']

            if tag in self._pid_to_unit_dicts[pid]:
                raise ValueError("m_unitTagIndex property of SUnitBornEvent or SUnitInitEvent shouldn't "
                                 "have been seen before.")

            self._pid_to_unit_dicts[pid][tag] = type_index
            self._current_state[type_index] += 1 if pid == 1 else -1
            self._total_units += 1
            self._current_state[self.game_loop_index] = event['_gameloop']
            self._append_normalized_current_state()
        elif event_type == "NNet.Replay.Tracker.SUnitTypeChangeEvent":
            type_name = str(event['m_unitTypeName'], 'utf-8')
            if type_name not in self._unit_type_to_index:
                return
            new_type_index = self._unit_type_to_index[type_name]
            tag = event['m_unitTagIndex']
            pid = None
            for i in self._pid_to_unit_dicts.keys():
                if tag in self._pid_to_unit_dicts[i]:
                    pid = i
                    break

            if pid is None:
                return

            original_type_index = self._pid_to_unit_dicts[pid][tag]

            self._pid_to_unit_dicts[pid][tag] = new_type_index
            self._current_state[original_type_index] -= 1 if pid == 1 else -1
            self._current_state[new_type_index] += 1 if pid == 1 else -1
            self._current_state[self.game_loop_index] = event['_gameloop']
            self._append_normalized_current_state()
        elif event_type == "NNet.Replay.Tracker.SUnitDiedEvent":
            tag = event['m_unitTagIndex']
            pid = None
            for i in self._pid_to_unit_dicts.keys():
                if tag in self._pid_to_unit_dicts[i]:
                    pid = i
                    break

            if pid is None:
                return

            original_type_index = self._pid_to_unit_dicts[pid][tag]
            self._pid_to_unit_dicts[pid].pop(tag)
            self._current_state[original_type_index] -= 1 if pid == 1 else -1
            self._current_state[self.game_loop_index] = event['_gameloop']
            self._total_units -= 1
            self._append_normalized_current_state()
        else:
            pass

    def convert_to_nparray(self):
        state_arrays = [np.reshape(np.asarray(s), newshape=(1, len(s))) for s in self.normalized_states]
        return np.concatenate(state_arrays, axis=0)

    @staticmethod
    def state_to_string(state):
        elements = ["RESULT: {0}".format(state[GameData.result_index])]
        if len(state) != GameData.n_state_indices:
            raise ValueError("Game state vectors must have {0} elements".format(GameData.n_state_indices))
        for i in range(GameData.n_unit_indices):
            type_names = [t for t in GameData._unit_type_to_index.keys() if GameData._unit_type_to_index[t] == i]
            elements.append("{0}: {1}".format("/".join(type_names), state[i]))

        return "{\n" + ",\n".join(map(lambda s: "\t" + s, elements)) + "\n}"

from datetime import date, datetime
import json
import os
from pathlib import Path
from time import sleep

import requests
import spotipy

import ssmi

import daemon
import signal
import lockfile

config_dir = str(Path.home()) + '/SSMI'
daemon_obj = None


# Read initialization files
def init():
    creds = load_creds()
    ss_data = steeelseries_load()
    if creds is None or ss_data is None:
        return None
    creds['address'] = ss_data['address']
    return creds


def load_creds():
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    if os.path.exists(config_dir + '/creds.json'):
        with open(config_dir + '/creds.json', 'r') as f:
            creds = json.load(f)
        return creds
    else:
        with open(config_dir + '/creds.json', 'w') as f:
            json.dump({'username': '', 'client_id': '', 'client_secret': ''}, f)
        write_log('Warning: No creds.json file found, failed to load credentials')
        return None


def steeelseries_load():
    path = '/Library/Application Support/SteelSeries Engine 3/coreProps.json'
    tries = 0
    while not os.path.exists(path) and tries < 5:
        tries += 1
        sleep(1)
    if not os.path.exists(path) and tries == 5:
        write_log('Error: Failed to load coreProps.json')
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    return data


# Write log
def write_log(msg):
    today = date.today()
    if not os.path.exists(config_dir + '/logs/'):
        os.mkdir(config_dir + '/logs/')
    with open(config_dir + '/logs/' + today.strftime("%d-%m-%Y") + '.txt', 'a') as f:
        f.write('[' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '] ' + msg + '\n')


# Shutdown signal
def shutdown(signum, frame):
    if daemon_obj is None:
        exit(0)
    else:
        daemon_obj.running = False


class SSMIUnix:
    def __init__(self, init_data: dict):
        self.dict_data = init_data

        self.target = 'http://' + self.dict_data['address'] + '/'
        try:
            ssmi.game_metadata(self.target, 'SSMI', 'SteelSeries Media Integration', 'Jack Hogan')
        except requests.exceptions.ConnectionError:
            sleep(60)
            try:
                ssmi.game_metadata(self.target, 'SSMI', 'SteelSeries Media Integration', 'Jack Hogan')
            except requests.exceptions.ConnectionError:
                write_log('Error: Failed to connect to SteelSeries Engine')
                return
        ssmi.bind_event(self.target, 'SSMI', 'UPDATE', 0, 100, 23)
        self.ss_login_status = True

        self.sp = spotipy.Spotify(client_credentials_manager=spotipy.SpotifyClientCredentials(client_id=
                                                                                              init_data['client_id'],
                                                                                              client_secret=
                                                                                              init_data[
                                                                                                  'client_secret']),
                                  auth=spotipy.util.prompt_for_user_token(init_data['username'], scope='user-read'
                                                                                                       '-currently'
                                                                                                       '-playing, '
                                                                                                       'user-read'
                                                                                                       '-playback-'
                                                                                                       'state',
                                                                          client_id=init_data['client_id'],
                                                                          client_secret=init_data['client_secret'],
                                                                          redirect_uri='http://localhost:8888/callback')
                                  )
        write_log('Info: SSMI init complete')

        self.running = True
        self.invalid_count = 0
        self.loop()

    def loop(self):
        write_log('Info: Initialization complete')
        while self.running:
            try:
                current = self.sp.current_playback()
            except spotipy.exceptions.SpotifyException:
                write_log('Error: Failed to refresh access token')
                return
            if self.invalid_count < 5 and \
                    (current is None or (current is not None and current['device']['type'] != 'Computer')):
                self.invalid_count += 1
            elif current is not None and current['device']['type'] == 'Computer':
                self.invalid_count = 0
            # Remove event when Spotify not open
            if self.invalid_count == 5:
                self.ss_login_status = False
                ssmi.remove_event(self.target, 'SSMI', 'UPDATE')
            # Rebind event if not bound already and Spotify connection OK
            elif not self.ss_login_status and self.invalid_count == 0:
                self.ss_login_status = True
                ssmi.bind_event(self.target, 'SSMI', 'UPDATE', 0, 100, 23)
            # Update screen if everything is good
            if self.ss_login_status and self.invalid_count == 0:
                title = current['item']['name']
                if len(title) > 14:
                    title = title[:11] + '...'
                artist, coartist_count = current['item']['artists'][0]['name'], len(current['item']['artists']) - 1
                if coartist_count > 0:
                    if len(artist) > 11:
                        artist = artist[:8] + '...'
                    artist += ' +' + str(coartist_count)
                elif len(artist) > 14:
                    artist = artist[:11] + '...'
                progress = int(current['progress_ms'] / current['item']['duration_ms'] * 100)
                ssmi.update_event(self.target, 'SSMI', 'UPDATE', title, artist, progress)
            else:
                # Keep alive if can't update
                ssmi.heartbeat(self.target, 'SSMI')
            sleep(0.5)
        write_log('Info: Graceful shutdown complete')


if __name__ == '__main__':
    init = init()
    if init is None:
        write_log('Error: Failed to initialize')
        exit(1)
    with daemon.DaemonContext(
        pidfile=lockfile.FileLock('/var/run/ssmi.pid'),
        signal_map={
            signal.SIGTERM: shutdown
        }
    ):
        daemon_obj = SSMIUnix(init)

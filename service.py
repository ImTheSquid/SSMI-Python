import json
import os
from datetime import date, datetime
from pathlib import Path
from time import sleep

import servicemanager
import spotipy
import spotipy.util as util
import win32event
import win32service
import win32serviceutil

import ssmi

config_dir = str(Path.home()) + '\\SSMI'


def writeLog(msg):
    today = date.today()
    if not os.path.exists(config_dir + '\\logs\\'):
        os.mkdir(config_dir + '\\logs\\')
    with open(config_dir + '\\logs\\' + today.strftime("%d-%m-%Y") + '.txt', 'a') as f:
        f.write('[' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '] ' + msg + '\n')


def load_creds():
    if os.path.exists(config_dir + '\\creds.json'):
        with open(config_dir + '\\creds.json', 'r') as f:
            creds = json.load(f)
        return creds
    else:
        with open(config_dir + '\\creds.json', 'w') as f:
            json.dump({'username': '', 'client_id': '', 'client_secret': ''}, f)
        return None


def steeelseries_load():
    path = os.getenv('PROGRAMDATA') + '\\SteelSeries\\SteelSeries Engine 3\\coreProps.json'
    tries = 0
    while not os.path.exists(path) and tries < 5:
        tries += 1
        sleep(1)
    if not os.path.exists(path) and tries == 5:
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    return data


class SSMIService(win32serviceutil.ServiceFramework):
    # Service control and SteelSeries
    ss_login_status = False
    running = False
    # Counts how many times a Spotify check returned 'None' or is on the wrong device
    invalid_count = 0
    target = ''
    _svc_name_ = 'SSMIService'
    _svc_display_name_ = 'SteelSeries Media Integration Service'
    _svc_description_ = 'Calls the SteelSeries Engine GameSense API to update current track info.'

    # Spotify
    # MAKE SURE THE CONFIG (creds.json) IS SET CORRECTLY
    sp = None

    @classmethod
    def parse_command_line(cls):
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args):
        super().__init__(args)

        writeLog('Service init')
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.running = False
        ssmi.remove_game(self.target, 'SSMI')
        writeLog('SSMI shutdown')

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.running = True
        # SteelSeries init
        ss_data = steeelseries_load()
        if ss_data is None:
            writeLog('Error: Couldn\'t load coreProps.json')
            return
        self.target = 'http://' + ss_data['address'] + '/'
        ssmi.game_metadata(self.target, 'SSMI', 'SteelSeries Media Integration', 'Jack Hogan')
        ssmi.bind_event(self.target, 'SSMI', 'UPDATE', 0, 100, 23)
        self.ss_login_status = True

        # Spotify init
        creds = load_creds()
        if creds is None:
            writeLog('Error: Couldn\'t load creds.json')
            return
        self.sp = spotipy.Spotify(client_credentials_manager=spotipy.SpotifyClientCredentials(client_id=
                                                                                              creds['client_id'],
                                                                                              client_secret=
                                                                                              creds['client_secret']),
                                  auth=util.prompt_for_user_token(creds['username'], scope='user-read-currently'
                                                                                           '-playing, '
                                                                                           'user-read-playback-state',
                                                                  client_id=creds['client_id'],
                                                                  client_secret=creds['client_secret'],
                                                                  redirect_uri='http://localhost:8888/callback'))
        writeLog('SSMI init complete')
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.loop()

    def loop(self):
        while self.running:
            current = self.sp.current_playback()
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
            sleep(0.5)


if __name__ == '__main__':
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    SSMIService.parse_command_line()

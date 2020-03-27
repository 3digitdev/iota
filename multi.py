import time
from multiprocessing import Process, Manager
from subprocess import Popen
import signal
import psutil


def play_song(files, shared):
    for file in files:
        print("playing", file)
        process = Popen(['mpg123', '--quiet', '-h 2', file])
        shared["pid"] = process.pid
        print("song: ", process.pid)
        process.wait()


if __name__ == "__main__":
    data = Manager().dict()
    player = Process(
        target=play_song, args=(['laugh.mp3', 'cough.mp3', 'pew.mp3'], data)
    )
    player.start()
    print("player: ", player.pid)
    time.sleep(1)
    print("pausing")
    psutil.Process(data["pid"]).send_signal(signal.SIGSTOP)
    time.sleep(2)
    print("resuming")
    psutil.Process(data["pid"]).send_signal(signal.SIGCONT)
    time.sleep(1)
    print("next song")
    psutil.Process(data["pid"]).send_signal(signal.SIGTERM)
    time.sleep(4)
    print("quitting")
    psutil.Process(data["pid"]).send_signal(signal.SIGTERM)
    player.terminate()
    """
    "player" would be the playlist manager
        This will spawn a single process that loops over some songs
        Pass in the list of "song ids"
        pass in a "shared resource"
        pass in the index to start at (default 0)
    "play_song" would manage the currently playing song
        store the index of the current song
        Loops over the list of song ids
        use the id to get the stream url
        run a Popen on the stream url to play the song with mpg123
        store the "song pid" in the shared resource

    Controls:
        "Pause/Resume" -- send SIGSTOP/SIGCONT to the "song pid"
        Next song -- send SIGTERM to the "song pid"
            this forces the loop to move to the next song id
            If the last song, the loop ends which will auto-quit the playlist!
        Previous song:
            grab index of current song, store it
            kill song and playlist
            restart playlist, setting the index to the stored index - 1
        Stop -- send SIGTERM to "song pid" and do playlist.terminate()
    """

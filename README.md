# Speech To Text To Speech Translation

This project handles local real-time audio to audio translation over sockets with OpenAI's Whisper and Microsoft SpeechT5 TTS. The project includes a client and server Python program, meaning that users can choose host the service on a high-performance GPU, then be able to use it on any consumer-level device.

Audio is sent by the client through WebSockets, which is transcribed into English with Whisper. SpeechT5 TTS then generates audio which reads off the transcription. The audio is sent back to the client and piped into any virtual audio device on their system. The end-to-end processing time is 1.5 seconds on an A100.

---

### Demo Video

[![Video Demonstration of Live Speech to Speech Translation](https://img.youtube.com/vi/yvikqjM8TeA/0.jpg)](https://www.youtube.com/watch?v=yvikqjM8TeA)

### Data flow

![Client Server Data Flow](https://github.com/kensonhui/live-speech-to-text-to-speech/assets/60726802/6a81c04e-c493-43d0-ad2e-a61638ddb81b)

### Server-side Flow

![Server Flow Diagram](https://github.com/kensonhui/live-speech-to-text-to-speech/assets/60726802/87ba0b85-6c7a-4cb6-bf19-f2fdf3722455)

Within the client, the user can pipe in the audio output to any virtual microphone or audio device they would like. One application is for video calls, the user can pipe the output to a virtual microphone, then use that audio device in a meeting so that everything they say is translated.

### Installation:

Ensure your ports specified in server.py is open! The default port we chose was 4444.

Install (FFmpeg)[https://www.ffmpeg.org/]:

```console
# macOS and Linux
sudo apt install ffmpeg

# Windows
winget install --id=Gyan.FFmpeg  -e
```

Install (uv)[https://docs.astral.sh/uv/]:

```console
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Running the application:

uv handles installing dependenices and running the application.

```console
# run server
uv run server

# run client
uv run client
```

### Notebooks for Testing

## speech.ipynb

Audiofile -> Translates to english text with whisper -> Create a synthesized voice with MS T5 TTS

## transcribe.ipynb

Microphone -> Transcribe to english text

## speech-to-transcribe

Microphone -> Translate and transcribe to english text

### Errors

`clang: error: no such file or directory: '/Users/kensonhui/anaconda3/envs/speech-to-speech/lib/python3.11/config-3.11-darwin/libpython3.11.a'`

or

`PY_SSIZE_T_CLEAN macro must be defined for '#' formats`

You'll have to update conda, update XCode, update brew, update your XCode CLI tools. Destroy your env, and rebuild your environment :D.

"""Server for real-time translation and voice synthesization."""

import select
import socket
from queue import Queue

import pyaudio
import torch
from rich.console import Console

from server.models.speech_recognition import SpeechRecognitionModel
from server.models.text_to_speech import TextToSpeechModel

console = Console()


class AudioSocketServer:
    """Class that handles real-time translation and voice synthesization.

    Socket input -> SpeechRecognition -> text -> TextToSpeech -> Socket output
    """

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 4096
    PORT = 4444
    # Number of unaccepted connections before server refuses new connections.
    #   For socket.listen()
    BACKLOG = 5

    def __init__(self, whisper_model: str = "base") -> None:
        """Initialize the server."""
        self.audio = pyaudio.PyAudio()
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Let kernel know we want to reuse the same port for restarting the
        #   server in quick succession
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: For multiple concurrent users we will need more queues for now
        #   we only want one user to work first
        self.data_queue: Queue = Queue()

        # Initialize the transcriber model
        self.transcriber = SpeechRecognitionModel(
            model_name=whisper_model,
            data_queue=self.data_queue,
            generation_callback=self.handle_generation,
            final_callback=self.handle_transcription,
        )
        self.text_to_speech = TextToSpeechModel(
            callback_function=self.handle_synthesize,
        )
        self.text_to_speech.load_speaker_embeddings()
        self.read_list = []

    def __del__(self) -> None:
        """Cleanup function for the server."""
        self.audio.terminate()
        self.transcriber.stop()
        self.serversocket.shutdown()
        self.serversocket.close()

    def handle_generation(self, packet: dict) -> None:
        """Transcription placeholder."""

    def handle_transcription(self, packet: str, client_socket: socket.socket) -> None:
        """Finalize transcriptions into TTS."""
        console.log(f"Added {packet} to synthesize task queue")
        self.text_to_speech.synthesise(packet, client_socket)

    def handle_synthesize(
        self,
        audio: torch.Tensor,
        client_socket: socket.socket,
    ) -> None:
        """Stream audio back to the client."""
        self.stream_numpy_array_audio(audio, client_socket)

    def start(self) -> None:
        """Start the server."""
        self.transcriber.start(16000, 2)
        console.log(f"Listening on port {self.PORT}")
        self.serversocket.bind(("", self.PORT))
        self.serversocket.listen(self.BACKLOG)
        # Contains all of the socket connections, the first is the server socket
        #   for listening to new connections. All other ones are for individual
        #   clients sending data.
        self.read_list = [self.serversocket]

        try:
            while True:
                readable, _, _ = select.select(self.read_list, [], [])
                for s in readable:
                    if s is self.serversocket:
                        (clientsocket, address) = self.serversocket.accept()
                        self.read_list.append(clientsocket)
                        console.log("Connection from", address)
                    else:
                        try:
                            data = s.recv(4096)

                            if data:
                                self.data_queue.put((s, data))
                            else:
                                self.read_list.remove(s)
                                console.log("Disconnection from", address)
                        except ConnectionResetError:
                            self.read_list.remove(s)
                            console.log("Client crashed from", address)
        except KeyboardInterrupt:
            pass
        console.log("Performing server cleanup")
        self.audio.terminate()
        self.transcriber.stop()
        self.serversocket.shutdown(socket.SHUT_RDWR)
        self.serversocket.close()
        console.log("Sockets cleaned up")

    def stream_numpy_array_audio(
        self,
        audio: torch.Tensor,
        client_socket: socket.socket,
    ) -> None:
        """Streams audio back to the client."""
        if client_socket is None:
            console.log("Error: client_socket is None")
            return
        try:
            client_socket.sendall(audio.numpy().tobytes())
        except ConnectionResetError as e:
            console.log(f"Error sending audio to client: {e}")
            if client_socket in self.read_list:
                self.read_list.remove(client_socket)


def main() -> None:
    """Start the server."""
    server = AudioSocketServer(whisper_model="base")
    server.start()


if __name__ == "__main__":
    main()
